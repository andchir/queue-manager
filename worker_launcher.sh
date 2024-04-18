#!/usr/bin/env bash
set -e
BASEDIR=$(dirname $0)
source "${BASEDIR}/venv/bin/activate"
python "${BASEDIR}/worker_launcher.py" python 2 workers/stable-diffusion-webui.py
