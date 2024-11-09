#!/bin/bash

WORKERS=('workers/live-portrait.py' 'workers/code-former.py' 'workers/face-swap.py' 'workers/photo-lip-sync.py')
WORKERS_NUM=(1, 1, 1, 1)

DIR="$(pwd)"
ACTION="none"

GREEN="\e[32m"
RED="\e[31m"
GRAY="\e[2m"
BLUE="\e[94m\e[1m"
NC="\e[0m"

source "${DIR}/venv/bin/activate"

if [ "$1" == "-h" ]; then
    echo -e "$NC"
    echo -e "${BLUE}Usage: ./$(basename "$0") status|start|stop"
    echo -e "$NC"
    exit 0
fi

if [ -n "$1" ]; then
    ACTION="$1"
fi

if [ $ACTION == 'status' ]; then
    echo -e "$NC"
    echo -e "${GRAY}-----------------------------------------"
    echo "                  STATUS                  "
    echo "-----------------------------------------"
    echo -e "$NC"

    PIDS="$(pidof "$DIR"/venv/bin/python)"
    IFS=' '
    read -ra PIDS_ARR <<< "$PIDS"

    for PID in "${PIDS_ARR[@]}"; do
        PS_OUT=$(ps "$PID" | grep 'python' --color=none)
        read -ra PS_OUT_ARR <<< "$PS_OUT"
        echo -e "${BLUE}${PS_OUT_ARR[5]}"
        echo -e "$NC"
    done
fi

if [ $ACTION == 'start' ]; then
    echo -e "$NC"
    echo -e "${GRAY}-----------------------------------------"
    echo "                  START                  "
    echo "-----------------------------------------"
    echo -e "$NC"


fi
