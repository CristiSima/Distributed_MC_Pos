import subprocess as sp
import time
import os

cc="gcc"

def my_system(args):
    sp.Popen(args, shell=True).wait()

def compile_c(core_count, overload_factor, local_offset, thread_count, world_limit, check_func=None):
    exec_name=f"compiled/main_c_{core_count}_{local_offset}_{thread_count}"
    my_system(f"{cc}  main.c -O2 -o {exec_name} "
        f" -D CORE_COUNT={core_count} "
        f" -D OVERLOAD_FACTOR={overload_factor} "
        f" -D LOCAL_OFFSET={local_offset} "
        f" -D THREAD_COUNT={thread_count} "
        f" -D WORLD_LIMIT={world_limit} "+
        (f" -D check_func={check_func} " if check_func else "")
    )

    return f"{exec_name}.exe"

def compile_cuda(block_count, core_count, overload_factor, local_offset, thread_count, world_limit, check_func=None):
    exec_name=f"compiled/main_cuda_{block_count}_{core_count}_{local_offset}_{thread_count}"
    my_system(f"nvcc main.cu -o {exec_name} "
        f" -D BLOCK_COUNT={block_count} "
        f" -D CORE_COUNT={core_count} "
        f" -D OVERLOAD_FACTOR={overload_factor} "
        f" -D LOCAL_OFFSET={local_offset} "
        f" -D THREAD_COUNT={thread_count} "
        f" -D WORLD_LIMIT={world_limit} "+
        (f" -D check_func={check_func} " if check_func else "")
    )

    return f"{exec_name}.exe"

def run_file(file_name):
    print(f"Running {file_name}")
    proc=sp.Popen([file_name,], stdout=sp.PIPE)
    start_time=time.perf_counter()
    proc.wait()
    run_time=time.perf_counter()-start_time
    print(f"Time {run_time}\n")
    # help(proc.stdout)
    return (run_time, proc.stdout.read().decode())

def bf_GPU_max_block_multiplyer(core_count, world_limit):
    duration=run_file(compile_cuda(1, core_count, 1, 0, core_count,  world_limit))[0]
    print("Base duration:", duration)
    for i in range(2, 100):
        new_duration=run_file(compile_cuda(i, core_count, 1, 0, i*core_count,  world_limit))[0]
        if(new_duration>duration):
            break
        duration=new_duration
        print("New  duration:", duration)

    i-=1
    print(f"Best duration  [{i}]:", duration)
    return i

class check_maker:
    def __init__(self, name="check_custom"):
        self.rules=[]
        self.name=name
    def add(self, pos, val):
        self.rules.append((pos, val))
    def gen(self):
        res=f'''
MODIFIER int {self.name}(int x, int y, int z)
{{
'''
        for (dx, dy, dz), eval in self.rules:
            res+=f"\tif(getQuads_inline(x+{dx}, y+{dy}, z+{dz}) != {eval}) return 0;\n"
        res+='''
\treturn 1;
}
'''
        return res
    def save(self):
        with open("custom.h", "w") as f:
            f.write(self.gen())


if __name__ == "__main__":
    maker=check_maker()
    square_length=4
    for i in range(square_length):
        for j in range(square_length):
            maker.add((i, 0, j), 0)
    maker.save()

    # bf_GPU_max_block_multiplyer(768, 100_000)
    # exit()
    block_multiplyer=6
    c_overload=70
    cuda_overload=1
    # a=compile_c(12, c_overload, 0, 12*c_overload, 100_000, "check_custom")
    tot,lim=120, 100_000
    # a=compile_c(12, 1, 0, tot, lim, "check_custom")
    # a=compile_cuda(6, 768, 0, 6*768,  60_000, "check_custom")
    # a=compile_cuda(block_multiplyer, 768, 0, block_multiplyer*768,  60_000, "check_custom")
    a=compile_cuda(block_multiplyer, 767, cuda_overload, 0, block_multiplyer*767*cuda_overload,  100_000, "check_custom")
    # a=compile_cuda(6, 768, 0, tot,lim, "check_custom")
    # a=compile_cuda(block_multiplyer, 768, 0, block_multiplyer*768,  1_000_000, "check_custom")
    print(a)
    # exit()
    print(*run_file(a), sep="\n")
