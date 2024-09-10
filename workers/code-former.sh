#!/bin/bash

source "/home/andrew/python_projects/CodeFormer/venv/bin/activate"

BASE_NAME=""$(basename $1)""
DIR_PATH="$(dirname "$1")"

echo "DIR_PATH: ${DIR_PATH}"
echo "BASE_NAME: ${BASE_NAME}"

python "/home/andrew/python_projects/CodeFormer/inference_codeformer.py" \
--input_path "$1" \
--upscale 2 \
--fidelity_weight 0.4 \
--bg_upsampler realesrgan \
--face_upsample \
--bg_upsampler realesrgan \
--bg_tile 400 \
--output_path "${DIR_PATH}/output"
