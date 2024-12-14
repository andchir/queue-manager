#!/bin/bash

DIR_PATH="/media/andrew/ADATA_512/python_projects/yolov8-face-landmarks-opencv-dnn"

source "$DIR_PATH""/venv/bin/activate"

cd "$DIR_PATH"

python main.py --imgpath "$1"
