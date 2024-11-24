#!/bin/bash

source "/home/andrew/python_projects/coqui-ai-TTS/venv/bin/activate"

python /home/andrew/python_projects/coqui-ai-TTS/clone_voice.py "$1" "$2"

echo "Done."
