import urllib3
import json
import os
import datetime

def send_sync_request(url: str, method: str, fields: object = None, body: object = None, headers: object = None, \
    timeout: int = 10, retries: (int, bool) = False) -> urllib3.response:

    http_pool = urllib3.PoolManager()

    # Define headers
    headers = {} if not headers else headers

    if body and isinstance(body, dict):
        headers['Content-Type'] = 'application/json'
        body = json.dumps(body).encode('utf-8')

    response = http_pool.request(method, url, fields=fields, body=body, headers = headers, timeout=timeout, retries=retries)

    return response

def notify(message, uuid, module_name: str = "ReEDS India 2.0", level="INFO"):

    notification_server = os.getenv('NOTIFIERHOST') if os.getenv('NOTIFIERHOST') != None else '127.0.0.1'
    notifier_port = os.getenv('NOTIFIERPORT') if os.getenv('NOTIFIERPORT') != None else "5002"

    body = {
        "time" : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "module_name": module_name,
        "message": message,
        "level": level
    }

    notification_url = f'http://{notification_server}:{notifier_port}/notifications/{uuid}'
    send_sync_request(notification_url, 'POST', body=body)