#!/bin/bash

source "/home/andrew/PycharmProjects/CodeFormer/venv/bin/activate"

BASE_NAME=""$(basename $1)""
DIR_PATH="$(dirname "$1")"

echo "DIR_PATH: ${DIR_PATH}"
echo "BASE_NAME: ${BASE_NAME}"

python "/home/andrew/PycharmProjects/CodeFormer/inference_codeformer.py" \
--input_path "$1" \
--upscale 2 \
--fidelity_weight 0.9 \
--bg_upsampler realesrgan \
--face_upsample \
--output_path "${DIR_PATH}/output"
