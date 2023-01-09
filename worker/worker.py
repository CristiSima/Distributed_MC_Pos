import json
import time
import urllib.request

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

    return response

with open("worker_info.json") as f:
    worker_info=json.load(f)

current_id=None
BASE_URL="http://192.168.0.200:5000/worker/"

current_id=None
def get_id():
    global current_id
    resp,resp_code = post(BASE_URL+"register", worker_info)
    current_id=resp["id"]
    print(resp)

get_id()

while True:
    resp,resp_code = get(BASE_URL+"sync/"+current_id)
    if resp_code==404:
        get_id()
    print(resp)
    time.sleep(5)
