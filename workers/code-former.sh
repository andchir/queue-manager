#!/bin/bash

source "/home/andrew/PycharmProjects/CodeFormer/venv/bin/activate"

BASE_NAME=""$(basename $1)""
DIR_PATH="$(dirname "$1")"

echo "DIR_PATH: ${DIR_PATH}"
echo "BASE_NAME: ${BASE_NAME}"

python "/home/andrew/PycharmProjects/CodeFormer/inference_codeformer.py" \
-w 0.7 --input_path "$1" \
--bg_upsampler realesrgan --face_upsample \
--output_path "${DIR_PATH}/output"
