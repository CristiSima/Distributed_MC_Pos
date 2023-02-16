from flask import Flask, Blueprint, request, render_template, redirect
from uuid import uuid1 as uuid, UUID
from threading import Lock
from copy import deepcopy
import tempfile
import shutil
import os
import base64
from importlib.machinery import SourceFileLoader
worker_lib= SourceFileLoader("worker_lib", "../worker/worker_lib.py").load_module()
import distribute
app = Flask(__name__)

worker = Blueprint('worker', __name__, url_prefix="/worker")
control = Blueprint('control', __name__, url_prefix="/control")
compile = Blueprint('compile', __name__, url_prefix="/compile")

def job_locked(func):
    def temp(*args, **kwargs):
        with job_lock:
            return func(*args, **kwargs)
    return temp

workers={}
class Worker:
    """docstring for Worker."""

    def __init__(self, cpu_info, gpu_info):
        self.id=uuid()

        self.cpu_info=cpu_info
        self.cpu_enabled=False
        self.cpu_working=False
        self.cpu_finished=False

        self.gpu_info=gpu_info
        self.gpu_enabled=False
        self.gpu_working=False
        self.gpu_finished=False

        workers[self.id]=self

        if cpu_info:
            cpu_info["overload_factor"]=cpu_info["estimated_duration"]=None
            cpu_info["id"]=self.id, "cpu"

        if gpu_info:
            gpu_info["overload_factor"]=gpu_info["estimated_duration"]=None
            gpu_info["id"]=self.id, "gpu"


    @job_locked
    def get_cpu_work(self):
        if not self.cpu_enabled:
            return "DISABLED"

        if self.cpu_working:
            return "WORKING"

        if not self.cpu_info["overload_factor"] or self.cpu_finished:
            return "JOB_DONE"

        overload_factor=self.cpu_info["overload_factor"]
        local_threads=overload_factor*self.cpu_info["core_count"]

        local_offset=job["threads_started"]
        job["threads_started"]=job["threads_started"]+local_threads

        self.cpu_working=True
        return {
            "local_offset": local_offset,
            "overload_factor": overload_factor,
            "local_threads": local_threads
        }

    @job_locked
    def get_gpu_work(self):
        if not self.gpu_enabled:
            return "DISABLED"

        if self.gpu_working:
            return "WORKING"

        if not self.gpu_info["overload_factor"] or self.gpu_finished:
            return "JOB_DONE"

        overload_factor=self.gpu_info["overload_factor"]
        local_threads=overload_factor*self.gpu_info["core_count"]

        local_offset=job["threads_started"]
        job["threads_started"]=job["threads_started"]+local_threads

        self.gpu_working=True
        return {
            "local_offset": local_offset,
            "overload_factor": overload_factor,
            "local_threads": local_threads
        }

job_lock=Lock()
job={
    "thread_count": None,
    "threads_started": 0,
    "threads_finished": 0,
    "state": "WAITING",

    "search_lim": 1_00_000,
    "y_level": -61,

    "estimated_duration": None,

    "check_func": None,
    "check_pattern": [
        [[0, 0, 0], 0],
    ],
}
org_job=deepcopy(job)
possitions=[]

def distribute_job():
    for worker in workers.values():
        worker.cpu_info["overload_factor"]=worker.gpu_info["overload_factor"]=None
        worker.cpu_info["estimated_duration"]=worker.gpu_info["estimated_duration"]=None

    job["estimated_duration"]=None
    job["thread_count"]=None

    units=[]
    for worker in workers.values():
        if worker.cpu_enabled:
            units.append(worker.cpu_info)
        if worker.gpu_enabled:
            units.append(worker.gpu_info)

    # print(units)
    if len(units) == 0:
        return

    time_mofier=pow(job["search_lim"]/100_000, 2)

    best_score=min(distribute.get_scores(units))
    overload_factors=[0]*len(units)
    for i, unit in enumerate(units):
        if unit["score"]==best_score:
            overload_factors[i]=1
    # print(best_score)
    # print(conf)
    overload_factors, work_time=distribute.complete_batch(units, overload_factors)

    work_time*=time_mofier
    estimated_durations=distribute.calc_proccessing_times(units, overload_factors)
    job["estimated_duration"]=round(work_time, 3)

    for overload_factor, unit, estimated_duration in zip(overload_factors, units, estimated_durations):
        estimated_duration*=time_mofier
        unit["overload_factor"]=overload_factor
        unit["estimated_duration"]=round(estimated_duration, 3)

    thread_distribution=distribute.get_thread_distribution(units, overload_factors)
    job["thread_count"]=sum(thread_distribution)


@worker.get('/debug')
def worker_debug():
    return {
        "A":2
    }


@worker.get('/sync/<worker_id>')
def worker_sync(worker_id):
    worker_id=UUID(worker_id)
    if worker_id not in workers:
        return {

        }, 404

    if job["state"]!="STARTED":
        return {
            **job,
            "gpu_work": None,
            "cpu_work": None,
            "start_flag": False,
        }, 200

    worker=workers[worker_id]

    cpu_work=worker.get_cpu_work()
    gpu_work=worker.get_gpu_work()

    start_flag=isinstance(cpu_work, dict) or isinstance(gpu_work, dict)

    return {
        **job,
        "gpu_work": gpu_work,
        "cpu_work": cpu_work,
        "start_flag": start_flag,
    }

@worker.post("/register")
def worker_register():
    worker=Worker(request.json["cpu"], request.json["gpu"])
    return {
        "result": "ok",
        "id": worker.id,
    }

@worker.post("/submit/<worker_id>/<target>")
def worker_submit(worker_id, target):
    worker_id=UUID(worker_id)

    for pos in request.json["possitions"]:
        possitions.append(pos)

    if worker_id not in workers:
        return {"error":"Unknown worker"}, 404

    worker=workers[worker_id]

    if target=="cpu":
        worker.cpu_working=False
        worker.cpu_finished=True
    else:
        worker.gpu_working=False
        worker.gpu_finished=True


    for pos in request.json["possitions"]:
        possitions.append(pos)

    job["threads_finished"]+=request.json["threads_processed"]

    if job["threads_finished"]==job["thread_count"]:
        job["state"]="FINISHED"


    return {
        "result": "ok",
        "id": worker.id,
    }


@control.get("/")
def control_index():
    distribute_job()
    return render_template("control.html.j2",
        workers=workers, job=job, possitions=possitions,
        len=len, round=round,
    )

@control.get("/possitions")
def control_possitions():
    distribute_job()
    return render_template("possitions.html.j2",
        workers=workers, job=job, possitions=possitions,
        len=len, round=round,
    )

@control.get("/pattern")
def control_pattern_intern():
    distribute_job()
    return render_template("pattern.html.j2",
        workers=workers, job=job, possitions=possitions,
        len=len, round=round, enumerate=enumerate, str=str, type=type, int=int,
    )

@control.get("/update_enabled/<worker_id>/gpu/<value>")
def control_update_enabled_gpu(worker_id, value):
    worker_id=UUID(worker_id)
    if worker_id not in workers:
        return redirect("/control")
    worker=workers[worker_id]

    worker.gpu_enabled=value=="True"

    return redirect("/control")

@control.get("/update_enabled/<worker_id>/cpu/<value>")
def control_update_enabled_cpu(worker_id, value):
    worker_id=UUID(worker_id)
    if worker_id not in workers:
        return redirect("/control")
    worker=workers[worker_id]

    worker.cpu_enabled=value=="True"

    return redirect("/control")

@control.get("/start_job")
def start_job():
    job["state"]="STARTED"
    job["threads_finished"]=0
    job["threads_started"]=0
    for worker in workers.values():
        worker.cpu_finished=False
        worker.gpu_finished=False
    return redirect("/control")

@control.get("/reset")
def reset_control():
    global workers
    global job
    workers={}
    job=deepcopy(org_job)

    return redirect("/control")

@control.post("/pattern_input")
def update_pattern_input():
    job["check_pattern"]=request.json

    return "OK"

@control.get("/pattern_input/reset")
def reset_pattern():
    job["check_pattern"]=[[[0, 0, 0], 0]]

    return redirect("/control/pattern")

@control.get("/pattern_select/")
@control.get("/pattern_select/<func_name>")
def select_pattern_func(func_name=None):
    job["check_func"]=func_name

    return redirect("/control/pattern")

@control.post("/y_level")
def control_y_level():

    if "target" in request.form:
        job["y_level"]=int(request.form["target_y"])

    if "range" in request.form:
        job["y_level"]=[
            int(request.form["min_y"]),
            int(request.form["max_y"]),
        ]

    return redirect("/control/pattern")


@compile.post("/c")
def compile_c():
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copy("../worker/base.h", temp_dir)
        shutil.copy("../worker/main.c", temp_dir)
        os.mkdir(f"{temp_dir}/compiled")

        check_maker=worker_lib.check_maker()
        for block_info in request.json["check_pattern"]:
            check_maker.add(*block_info)
        check_maker.save(cwd=temp_dir)

        compile_args=request.json["compile_args"]
        # TODO some validation should be done here
        exec_name=worker_lib.compile_c(**compile_args, cwd=temp_dir)

        with open(f"{temp_dir}/{exec_name}", "rb") as f:
            b64_exec=base64.b64encode(f.read()).decode()

        return {
            "exec_name": exec_name,
            "b64_exec": b64_exec
        }



@compile.post("/cuda")
def compile_cuda():
    with tempfile.TemporaryDirectory() as temp_dir:
        shutil.copy("../worker/base.h", temp_dir)
        shutil.copy("../worker/main.cu", temp_dir)
        os.mkdir(f"{temp_dir}/compiled")

        check_maker=worker_lib.check_maker()
        for block_info in request.json["check_pattern"]:
            check_maker.add(*block_info)
        check_maker.save(cwd=temp_dir)

        compile_args=request.json["compile_args"]
        # TODO some validation should be done here
        exec_name=worker_lib.compile_cuda(**compile_args, cwd=temp_dir)

        with open(f"{temp_dir}/{exec_name}", "rb") as f:
            b64_exec=base64.b64encode(f.read()).decode()

        return {
            "exec_name": exec_name,
            "b64_exec": b64_exec
        }

'''

features:
    manage workers
        register
        distribute work(maybe smart)

    get job from user
    display cluster info
    display job result

excesive:
    persistense
    worker_timeout(maybe desconnect all)

worker api:
    /register
    /get_updates(job) sync
    /submit

'''

app.register_blueprint(worker)
app.register_blueprint(control)
app.register_blueprint(compile)
if __name__=="__main__":
    app.run(host="0.0.0.0", debug=True)
