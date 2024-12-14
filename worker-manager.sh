#!/bin/bash

WORKERS=('workers/live-portrait.py' 'workers/code-former.py' 'workers/face-swap.py' 'workers/photo-lip-sync.py' 'workers/xtts_create.py' 'workers/xtts_clone.py')
WORKERS_NUM=(1 1 1 1 1 1)
QUEUE_SIZE_URLS=('https://queue.api2app.ru/queue_size/fe10d225-fbae-47b8-9e13-9beb9c1890b8' 'https://queue.api2app.ru/queue_size/8c595969-139a-40ec-87f5-f523d02f7f4a')

DIR="$(pwd)"
ACTION="none"

GREEN="\e[32m"
RED="\e[31m"
GRAY="\e[2m"
BLUE="\e[94m\e[1m"
NC="\e[0m"
BOLD="\e[1m"

source "${DIR}/venv/bin/activate"

if [ "$1" == "-h" ]; then
    echo -e "$NC"
    echo -e "${BLUE}Usage: ./$(basename "$0") status|start|stop"
    echo -e "$NC"
    exit 0
fi

if [ -n "$1" ]; then
    ACTION="$1"
else
    exit 0
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

PIDS="$(pidof python)"
echo -e "${BLUE}PIDs: ${PIDS}""$NC"
IFS=' '
read -ra PIDS_ARR <<< "$PIDS"

PS_ARR=()

for PID in "${PIDS_ARR[@]}"; do
    PS_OUT=$(ps "$PID" | grep 'python' --color=none)
    read -ra PS_OUT_ARR <<< "$PS_OUT"
    PS_ARR=("${PS_ARR[@]}" "${PS_OUT_ARR[5]}")
done

if [ $ACTION == 'status' ]; then
    echo -e "$NC"
    echo -e "${GRAY}-----------------------------------------"
    echo "                  STATUS                  "
    echo "-----------------------------------------"
    echo -e "$NC"

    for worker_name in "${WORKERS[@]}"; do
        count=$(count_items "$worker_name" "${PS_ARR[@]}")
        if [[ "$count" -lt "${WORKERS_NUM[$i]}" ]]; then
            echo -e "${RED}- ${worker_name} [${count}]"
        else
            echo -e "${GREEN}- ${worker_name} [${count}]"
        fi
        echo -e "$NC"
    done

    for queue_size_url in "${QUEUE_SIZE_URLS[@]}"; do
        # echo -e "${GRAY}Queue URL: ${queue_size_url}"
        queue_size=$(curl -s "$queue_size_url" | python3 -c "import sys, json; print(json.load(sys.stdin)['queue_size'])")
        echo -e "${GRAY}Queue size: ${queue_size}"
    done
    echo -e "$NC"
fi

if [ $ACTION == 'start' ]; then
    echo -e "$NC"
    echo -e "${GRAY}-----------------------------------------"
    echo "                  START                  "
    echo "-----------------------------------------"
    echo -e "$NC"

    STARTED_COUNT=0
    i=0
    for worker_name in "${WORKERS[@]}"
    do
        count=$(count_items "$worker_name" "${PS_ARR[@]}")
        NUM=$((WORKERS_NUM[$i] - count))
        if [[ "$count" -lt "${WORKERS_NUM[$i]}" ]]; then

            for (( j=0; j<${NUM}; j++ )); do
                echo -e "${GRAY}${BOLD}Starting${NC} ${worker_name}"
                nohup python "${worker_name}" > "${worker_name/\//_}"_log.txt 2>&1 &
                ((STARTED_COUNT++))
            done

        fi
        ((i++))
    done

    echo -e "${GREEN}Started: ${STARTED_COUNT}"
fi

if [ $ACTION == 'stop' ]; then
    echo -e "$NC"
    echo -e "${GRAY}-----------------------------------------"
    echo "                  STOP                  "
    echo "-----------------------------------------"
    echo -e "$NC"

    STOPPED_COUNT=0

    for PID in "${PIDS_ARR[@]}"; do
        PS_OUT=$(ps "$PID" | grep 'python' --color=none)
        read -ra PS_OUT_ARR <<< "$PS_OUT"
        for worker_name in "${WORKERS[@]}"; do
            if [ "$worker_name" == "${PS_OUT_ARR[5]}" ]; then
                echo -e "${GRAY}${BOLD}Stopping ${PID}${NC}" "${PS_OUT_ARR[5]}"
                kill "$PID"
                ((STOPPED_COUNT++))
            fi
        done
    done

    echo -e "${GREEN}Stopped: ${STOPPED_COUNT}"
fi
