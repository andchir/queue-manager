#!/bin/bash

source "/home/andrew/python_projects/coqui-ai-TTS/venv/bin/activate"
export TTS_HOME="/home/andrew/python_projects/coqui-ai-TTS/.local"

cd /home/andrew/python_projects/coqui-ai-TTS
python use_cloned_voice.py "$1" "$2" "$3" "$4"
