from flask import Flask, Blueprint, request, render_template, redirect
from uuid import uuid1 as uuid, UUID
from threading import Lock
from copy import deepcopy
import distribute
app = Flask(__name__)

worker = Blueprint('worker', __name__, url_prefix="/worker")
control = Blueprint('control', __name__, url_prefix="/control")

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

        cpu_info["scheduled_threads"]=cpu_info["estimated_duration"]=None
        gpu_info["scheduled_threads"]=gpu_info["estimated_duration"]=None

        cpu_info["id"]=self.id, "cpu"
        gpu_info["id"]=self.id, "gpu"

    @job_locked
    def get_cpu_work(self):
        if not self.cpu_enabled:
            return "DISABLED"

        if self.cpu_working:
            return "WORKING"

        if not self.cpu_info["scheduled_threads"] or self.cpu_finished:
            return "JOB_DONE"

        threads_no=self.cpu_info["scheduled_threads"]

        threads_offset=job["threads_started"]
        job["threads_started"]=job["threads_started"]+threads_no

        self.cpu_working=True
        return {
            "threads_offset":threads_offset,
            "threads":threads_no
        }

    @job_locked
    def get_gpu_work(self):
        if not self.gpu_enabled:
            return "DISABLED"

        if self.gpu_working:
            return "WORKING"

        if not self.gpu_info["scheduled_threads"] or self.gpu_finished:
            return "JOB_DONE"

        threads_no=self.gpu_info["scheduled_threads"]

        threads_offset=job["threads_started"]
        job["threads_started"]=job["threads_started"]+threads_no

        self.gpu_working=True
        return {
            "threads_offset":threads_offset,
            "threads":threads_no
        }

job_lock=Lock()
job={
    "no_threads": None,
    "threads_started": 0,
    "threads_finished": 0,
    "started": False,

    "search_lim": 2_00_000,

    "estimated_duration": None,

    # "check_func": None,
    "check_func": [
        ((0, 0, 0), 0),
    ],
}
org_job=deepcopy(job)
possitions=[]

def distribute_job():
    for worker in workers.values():
        worker.cpu_info["scheduled_threads"]=worker.gpu_info["scheduled_threads"]=None
        worker.cpu_info["estimated_duration"]=worker.gpu_info["estimated_duration"]=None

    job["estimated_duration"]=None
    job["no_threads"]=None

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
    for i, unit in enumerate(units):
        if unit["score"]==best_score:
            conf=[0]*len(units)
            conf[i]=unit["cores"]
    # print(best_score)
    # print(conf)
    conf, best_time=distribute.complete_batch(conf, units)
    best_time*=time_mofier
    # print(conf, best_time)
    # print(distribute.calc_proccessing_delta(units, conf))
    for scheduled_threads, unit, unit_duration in zip(conf, units, distribute.calc_proccessing_times(units, conf)):
        unit_duration*=time_mofier
        unit["scheduled_threads"]=scheduled_threads
        unit["estimated_duration"]=round(unit_duration, 3)

    job["estimated_duration"]=round(best_time, 3)
    job["no_threads"]=sum(conf)


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

    if not job["started"]:
        return {
            **job,
            "gpu_work": None,
            "cpu_work": None,
        }, 200

    worker=workers[worker_id]

    if worker.cpu_info["score"]<worker.gpu_info["score"]:
        cpu_work=worker.get_cpu_work()
        gpu_work=worker.get_gpu_work()
    else:
        gpu_work=worker.get_gpu_work()
        cpu_work=worker.get_cpu_work()

    return {
        **job,
        "gpu_work":gpu_work,
        "cpu_work":cpu_work,
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
    job["started"]=True
    return redirect("/control")

@control.get("/reset")
def reset_control():
    global workers
    global job
    workers={}
    job=deepcopy(org_job)
    return redirect("/control")

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
if __name__=="__main__":
    app.run(host="0.0.0.0", debug=True)
