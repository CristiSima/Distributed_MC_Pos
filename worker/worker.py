import json
import time
import urllib.request
from queue import Queue
from threading import Thread, Event
from time import sleep
import worker_lib

def roundup(nr):    return (int(nr) if nr == round(nr) else int(nr)+1)

def get(url, headers=None):
    headers = headers or {}
    headers = {"Accept": "application/json", **headers}

    httprequest = urllib.request.Request(
        url, headers=headers, method="GET"
    )

    try:
        with urllib.request.urlopen(httprequest) as httpresponse:
            return json.loads(httpresponse.read().decode(
                httpresponse.headers.get_content_charset("utf-8")
            )), httpresponse.status
    except urllib.error.HTTPError as e:
        return None, 404
    except urllib.error.URLError as e:
        return None, 404

    return response

def post(url, json_payload=None, headers=None):
    headers = headers or {}
    headers = {"Accept": "application/json", **headers}

    request_data =None

    if json_payload:
        request_data = json.dumps(json_payload).encode()
        headers["Content-Type"] = "application/json; charset=UTF-8"

    httprequest = urllib.request.Request(
        url, data=request_data, headers=headers, method="POST"
    )

    try:
        with urllib.request.urlopen(httprequest) as httpresponse:
            return json.loads(httpresponse.read().decode(
                httpresponse.headers.get_content_charset("utf-8")
            )), httpresponse.status
    except urllib.error.HTTPError as e:
        return None, 404
    except urllib.error.URLError as e:
        return None, 404

    return response

with open("worker_info.json") as f:
    worker_info=json.load(f)

current_id=None
BASE_URL="http://192.168.0.200:5000/worker/"

current_id=None
def get_id():
    global current_id
    resp,resp_code = post(BASE_URL+"register", worker_info)
    if resp_code==200:
        current_id=resp["id"]
    print(resp)

def create_processor(func):
    queue=Queue()

    def thread_loop():
        while True:
            func(queue.get())

    thread=Thread(target=thread_loop)

    return queue, thread

def cpu_process(job):
    cpu_work=job["cpu_work"]
    if not isinstance(cpu_work, dict):
        return

    print("cpu", cpu_work)
    exec_name=worker_lib.compile_c(
        num_threads=cpu_work["workers"],
        thread_overload=1,
        worker_offset=cpu_work["workers_offset"],
        total_workers=job["no_threads"],
        world_limit=job["search_lim"],
        check_func=None
    )
    print(exec_name)
    duration, output=worker_lib.run_file(exec_name)
    print(f"CPU Took: {duration}", output, sep="\n")
    possitions=[line[8:] for line in output.split("\n") if line.startswith("FOUND")]
    possitions=[list(map(int,pos.split(" "))) for pos in possitions]
    print("possitions:", possitions)
    post(BASE_URL+f"submit/{current_id}/cpu", {
        "possitions": possitions,
        "threads_processed": cpu_work["workers"]
    })
cpu_queue, cpu_thread=create_processor(cpu_process)
cpu_thread.start()

def gpu_process(job):
    gpu_work=job["gpu_work"]
    if not isinstance(gpu_work, dict):
        return

    print("gpu", gpu_work)
    print(gpu_work["workers"]/worker_info["gpu"]["block_dim"])
    exec_name=worker_lib.compile_cuda(
        num_blocks=roundup(gpu_work["workers"]/worker_info["gpu"]["block_dim"]),
        num_threads=worker_info["gpu"]["block_dim"],
        thread_overload=1,
        worker_offset=gpu_work["workers_offset"],
        total_workers=job["no_threads"],
        world_limit=job["search_lim"],
        check_func=None
    )
    print(exec_name)
    duration, output=worker_lib.run_file(exec_name)
    print(f"GPU Took: {duration}", output, sep="\n")
    possitions=[line[8:] for line in output.split("\n") if line.startswith("FOUND")]
    possitions=[list(map(int,pos.split(" "))) for pos in possitions]
    print("possitions:", possitions)
    post(BASE_URL+f"submit/{current_id}/gpu", {
        "possitions": possitions,
        "threads_processed": gpu_work["workers"]
    })
gpu_queue, gpu_thread=create_processor(gpu_process)
gpu_thread.start()


while not current_id:
    get_id()

while True:
    resp,resp_code = get(BASE_URL+"sync/"+current_id)
    if resp_code==404:
        get_id()

    cpu_queue.put(resp)

    gpu_queue.put(resp)


    print(resp)
    time.sleep(5)
