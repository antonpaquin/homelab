#!/bin/bash

set -ex

cd /opt/stable-diffusion/stable-diffusion-webui
source venv/bin/activate

pip install -r repositories/CodeFormer/requirements.txt
pip install -r requirements.txt
