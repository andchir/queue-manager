#!/bin/bash

WORKERS=('workers/live-portrait.py' 'workers/code-former.py' 'workers/face-swap.py' 'workers/photo-lip-sync.py')
WORKERS_NUM=(1, 1, 1, 1)
WORKERS_NUM_CURRENT=(0, 0, 0, 0)

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

function count_items() {
    local search_item=$1
    shift
    local array=("$@")
    local COUNT=0
    for i in "${array[@]}"; do
        if [ "$i" == "$search_item" ]; then
            COUNT=$(expr $COUNT + 1)
        fi
    done
    echo "$COUNT"
}

if [ $ACTION == 'status' ]; then
    echo -e "$NC"
    echo -e "${GRAY}-----------------------------------------"
    echo "                  STATUS                  "
    echo "-----------------------------------------"
    echo -e "$NC"

    PIDS="$(pidof python)"
    echo -e "${BLUE}PIDs: ${PIDS}"
    echo -e "$NC"
    IFS=' '
    read -ra PIDS_ARR <<< "$PIDS"

    PS_ARR=()

    for PID in "${PIDS_ARR[@]}"; do
        PS_OUT=$(ps "$PID" | grep 'python' --color=none)
        read -ra PS_OUT_ARR <<< "$PS_OUT"
        PS_ARR=("${PS_ARR[@]}" "${PS_OUT_ARR[5]}")
    done

    for worker_name in "${WORKERS[@]}"; do
        count=$(count_items "$worker_name" "${PS_ARR[@]}")
        if [ $count != 0 ]; then
            echo -e "${GREEN}- ${worker_name} [${count}]"
        else
            echo -e "${RED}- ${worker_name} [0]"
        fi
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
