#!/usr/bin/env bash
set -e
BASEDIR=$(dirname $0)
cd $BASEDIR
source "venv/bin/activate"
python "worker_launcher.py" python 2 workers/stable-diffusion-webui.py
