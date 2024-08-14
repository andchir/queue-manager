#!/bin/bash

source "/home/andrew/python_projects/LivePortrait/venv/bin/activate"

BASE_NAME=""$(basename $1)""
DIR_PATH="$(dirname "$1")"

echo "DIR_PATH: ${DIR_PATH}"
echo "BASE_NAME: ${BASE_NAME}"

python "/home/andrew/python_projects/LivePortrait/inference.py" \
--source "$1" \
--driving "$2" \
--output-dir "${DIR_PATH}/output"
