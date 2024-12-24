from datetime import datetime
from urllib.parse import quote_plus
import requests
import os
import sys
import time

project = os.environ.get('GITLAB_SIGNING_PROJECT')
trigger_token = os.environ.get("GITLAB_TRIGGER_TOKEN")
access_token = os.environ.get("GITLAB_ACCESS_TOKEN")

if not project or not trigger_token or not access_token:
    print('GITLAB_SIGNING_PROJECT, GITLAB_TRIGGER_TOKEN, and GITLAB_ACCESS_TOKEN required')
    sys.exit(1)

project = quote_plus(project)

def retry(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"Internal error, retrying: {e}")
        time.sleep(30)
        return retry(func, args, **kwargs)

def start(device, version, type_, pipeline_id):
    gitlab_url = f"https://gitlab.com/api/v4/projects/{project}/trigger/pipeline?token={trigger_token}&ref=master"
    data = {
        "variables[DEVICE]": device,
        "variables[PIPELINE_ID]": pipeline_id,
        "variables[VERSION]": version,
        "variables[RELEASE_TYPE]": type_
    }
    req = requests.post(gitlab_url, data)
    if req.status_code == 201:
        print("Started at ", req.json()['web_url'])
        return req.json()['id']
    else:
        print("ERROR", req.status_code, req.text)

def main():
    pipeline_id = start(os.environ.get("DEVICE"), os.environ.get("VERSION"), os.environ.get("RELEASE_TYPE"), os.environ.get("CI_PIPELINE_ID"))
    status = "pending"
    gitlab_url = f"https://gitlab.com/api/v4/projects/{project}/pipelines/{pipeline_id}"
    headers = {'Private-Token': access_token}
    while True:
        resp = retry(requests.get, gitlab_url, headers=headers)
        if resp.status_code == 200:
            status = resp.json().get("status")
            if status == "success":
                print("SUCCESS")
                sys.exit(0)
            elif status == "pending" or status == "running":
                print("Still waiting...")
                pass
            else:
                print("FAILURE")
                print(status)
                sys.exit(1)
        time.sleep(10)

if __name__ == '__main__':
    main()

