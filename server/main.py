from flask import Flask, Blueprint, request, render_template, redirect
from uuid import uuid1 as uuid, UUID
from threading import Lock
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
        self.cpu_enabled=True
        self.cpu_working=False

        self.gpu_info=gpu_info
        self.gpu_enabled=True
        self.gpu_working=False

        workers[self.id]=self

    @job_locked
    def get_cpu_work(self):
        if self.cpu_working:
            return "WORKING"

        threads_left=max(job["no_threads"]-job["threads_started"], 0)
        if threads_left == 0:
            return "JOB_DONE"

        workers_no=min(threads_left, self.cpu_info["cores"])

        workers_offset=job["threads_started"]
        job["threads_started"]=job["threads_started"]+workers_no

        self.cpu_working=True
        return {
            "workers_offset":workers_offset,
            "workers":workers_no
        }

    @job_locked
    def get_gpu_work(self):
        print("gpu work", self.gpu_working)
        if self.gpu_working:
            return "WORKING"

        threads_left=max(job["no_threads"]-job["threads_started"], 0)
        if threads_left == 0:
            return "JOB_DONE"

        workers_no=min(threads_left, self.gpu_info["cores"])

        workers_offset=job["threads_started"]
        job["threads_started"]=job["threads_started"]+workers_no

        self.gpu_working=True
        return {
            "workers_offset":workers_offset,
            "workers":workers_no
        }

job_lock=Lock()
job={
    "no_threads":20000,
    "threads_started":2,
}

@worker.get('/debug')
def worker_debug():
    return {
        "A":2
    }


@worker.get('/sync/<worker_id>')
def worker_sync(worker_id):
    worker_id=UUID(worker_id)
    print(worker_id)
    if worker_id not in workers:
        return {

        }, 404

    worker=workers[worker_id]

    if worker.cpu_info["score"]<worker.gpu_info["score"]:
        cpu_work=worker.get_cpu_work()
        gpu_work=worker.get_gpu_work()
    else:
        gpu_work=worker.get_gpu_work()
        cpu_work=worker.get_cpu_work()

    print(worker.cpu_working, worker.gpu_working)

    return {
        "gpu_work":gpu_work,
        "cpu_work":cpu_work,
    }

@worker.post("/register")
def worker_register():
    print(request.json)
    worker=Worker(request.json["cpu"], request.json["gpu"])
    return {
        "result": "ok",
        "id": worker.id,
    }

@worker.post("/submit/<worker_id>")
def worker_submit(worker_id):
    print(request.data)
    return {
        "result": "ok",
        "id": worker.id,
    }


@control.get("/")
def control_index():
    return render_template("control.html.j2", workers=workers)

@control.get("/update_enabled/<worker_id>/gpu/<value>")
def control_update_enabled_gpu(worker_id, value):
    worker_id=UUID(worker_id)
    if worker_id not in workers:
        return redirect("/control")
    worker=workers[worker_id]

    print(type(value))
    worker.gpu_enabled=value=="True"

    return redirect("/control")

@control.get("/update_enabled/<worker_id>/cpu/<value>")
def control_update_enabled_cpu(worker_id, value):
    worker_id=UUID(worker_id)
    if worker_id not in workers:
        return redirect("/control")
    worker=workers[worker_id]

    print(type(value))
    worker.cpu_enabled=value=="True"

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
