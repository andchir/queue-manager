#!/bin/bash

source "/home/andrew/python_projects/insightface/venv/bin/activate"

BASE_NAME="$(basename "$1")"
DIR_PATH="$(dirname "$1")"

echo "DIR_PATH: ${DIR_PATH}"
echo "BASE_NAME: ${BASE_NAME}"

python "/home/andrew/python_projects/insightface/face_swap.py" \
--input "$1" \
--face_input "$2" \
--output "${DIR_PATH}/output/${BASE_NAME}"
