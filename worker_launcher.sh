#!/usr/bin/env bash

# use Cron:
# */1 * * * * /home/andrew/PycharmProjects/queue-manager/worker_launcher.sh

set -e
BASEDIR=$(dirname $0)
cd $BASEDIR
source "venv/bin/activate"
python "worker_launcher.py" python 2 workers/stable-diffusion-webui.py
