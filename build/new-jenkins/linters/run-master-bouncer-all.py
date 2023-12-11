#!/usr/bin/env python3

import subprocess
import json
import urllib.request as http
import os
import base64
import pprint

DEBUG = os.environ.get('DEBUG', '0') == '1'
workspace = os.environ['WORKSPACE']
gerrit_host = os.environ['GERRIT_HOST']
ssh_key_path = os.environ.get('SSH_KEY_PATH')
ssh_username = os.environ.get('SSH_USERNAME')
master_bouncer_key = os.environ['MASTER_BOUNCER_KEY']
authorization = (
    base64.encodebytes(f"master_bouncer:{master_bouncer_key}".encode())
    .decode()
    .strip()
)

def fp(message):
    print(message, flush=True)

def cmd_exec(command, **kwargs):
    fp(f"> {command}")
    fetch_environment = os.environ.copy()
    if ssh_key_path and ssh_username:
        fetch_environment['GIT_SSH_COMMAND'] = 'ssh -i $SSH_KEY_PATH -l $SSH_USERNAME'
    code = subprocess.call(command, stderr=subprocess.STDOUT, shell=True, env=fetch_environment, **kwargs)
    if code != 0:
        exit(code)

def git_fetch(info):
    cmd_exec(f'git fetch ssh://{gerrit_host}:29418/canvas-lms {info["refspec"]}')

def gerrit_get(path):
    url = f"https://{gerrit_host}/{path}"
    request = http.Request(
        url, headers={'Authorization': f'Basic {authorization}'}
    )
    response = http.urlopen(request)
    return json.loads(response.read().decode('utf8').split(")]}'")[1])

def perform_check(info):
    command = [
        "docker run",
        "--volume $WORKSPACE/.git:/app/.git",
        f"--env MASTER_BOUNCER_KEY={master_bouncer_key}",
        "--env GERGICH_REVIEW_LABEL=Lint-Review",
        f"--env GERRIT_HOST={gerrit_host}",
        "--env GERRIT_PROJECT=canvas-lms",
        f'--env GERRIT_BRANCH={info["branch"]}',
        f'--env GERRIT_PATCHSET_REVISION={info["sha"]}',
        f'--env GERRIT_CHANGE_ID={info["change_id"]}',
        f'--env GERRIT_PATCHSET_NUMBER={info["change_number"]}',
        "--entrypoint master_bouncer",
        "instructure/gergich check",
    ]
    cmd_exec(' '.join(command))

def main():
    all_changes = gerrit_get("a/changes/?q=status:open+p:canvas-lms+label:Verified=1+is:mergeable+branch:master&o=CURRENT_REVISION")
    for change in all_changes:
        if "wip" in change["subject"].lower():
            continue
        info = {
            "sha": change["current_revision"],
            "refspec": change['revisions'][change["current_revision"]]['ref'],
            "change_number": change['revisions'][change["current_revision"]]['_number'],
            "change_id": change["change_id"],
            "branch": change["branch"]
        }
        fp(">> ==================================================")
        fp(f">> checking change: {info}")
        if (DEBUG):
            pprint.pprint(change)
        git_fetch(info)
        perform_check(info)
        fp("")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        fp("")
