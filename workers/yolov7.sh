#!/bin/bash

DIR_PATH="/media/andrew/256GB/python_projects/yolov7"

source "$DIR_PATH""/venv/bin/activate"

cd "$DIR_PATH"

python detect.py --weights yolov7.pt \
--conf 0.25 --img-size 640 \
--source "$1" \
--device 0 \
--no-trace --nosave --conf-thres 0.8
