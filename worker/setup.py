import worker_lib
import worker
import os
import json

BENCHMARK_WORLD_LIMIT=100_000

def setup_cpu():
    print("Seting up the CPU")

    cpu_cores=os.cpu_count()
    print(f"FOUND {cpu_cores} cores")

    print("Benchmarking...")
    print("Compiling Benchmark")
    exec_path=worker.compile_c(
        core_count=cpu_cores,
        overload_factor=1, local_offset=0,
        thread_count=cpu_cores,
        world_limit=BENCHMARK_WORLD_LIMIT,
    )
    print("Running Benchmark")
    runtime, _= worker_lib.run_file(exec_path)

    cpu_info={
        "core_count":cpu_cores,
        "score":round(runtime, 3),
    }

    return cpu_info

def setup_gpu():
    print("Seting up the GPU")

    print("Compiling setup.cu")
    # os.system("nvcc setup.cu      -o compiled/setup")

    print("Running setup.cu")
    _, setup_output=worker_lib.run_file("./compiled/setup")
    print(setup_output)

    mp_count=int(setup_output.split("\n")[1].split(" ")[-1])
    threads_per_block=int(setup_output.split("\n")[2].split(" ")[-1])
    sp_cores=int(setup_output.split("\n")[3].split(" ")[-1])

    print("Compiling benchmark")
    benchmark_exec=worker.compile_cuda(
        block_count=mp_count,
        core_count=threads_per_block,
        overload_factor=1,
        local_offset=0,
        thread_count=mp_count*threads_per_block,
        world_limit=BENCHMARK_WORLD_LIMIT
    )

    print("Warming up the GPU")
    _,_=worker_lib.run_file(benchmark_exec)

    print("Benchmarking")
    run_time1,_=worker_lib.run_file(benchmark_exec)
    run_time2,_=worker_lib.run_file(benchmark_exec)
    run_time3,_=worker_lib.run_file(benchmark_exec)

    run_time=round((run_time1+run_time2+run_time3)/3,3)

    return {
        "core_count": mp_count*threads_per_block,
        "block_size": threads_per_block,
        "block_count": mp_count,
        "score": run_time
    }

def user_wants_gpu():
    while True:
        resp=input("Configure GPU?(y/n) ")

        if resp not in ["y", "Y", "n", "N"]:
            continue

        return resp in ["y", "Y"]

config_gpu=False
config_gpu=user_wants_gpu()

print()

info={
    "cpu":setup_cpu(),
    "gpu":setup_gpu() if config_gpu else None
}

print(info)
with open("worker_info.json", "w") as f:
    json.dump(info, f, indent=4)
