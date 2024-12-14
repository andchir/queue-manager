#!/bin/bash

source "/media/andrew/ADATA_512/python_projects/comfyui-api/venv/bin/activate"

cd "/media/andrew/ADATA_512/python_projects/comfyui-api"
python basic_api.py "DDColor.json" "$1"
