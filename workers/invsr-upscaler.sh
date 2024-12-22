#!/bin/bash

source "/home/andrew/python_projects2/InvSR/venv/bin/activate"

BASE_NAME=""$(basename $1)""
DIR_PATH="$(dirname "$1")"

echo "DIR_PATH: ${DIR_PATH}"
echo "BASE_NAME: ${BASE_NAME}"

cd "/home/andrew/python_projects2/InvSR"
python "inference_invsr.py" \
-i "$1" \
-o "${DIR_PATH}/output" \
--num_steps 1
