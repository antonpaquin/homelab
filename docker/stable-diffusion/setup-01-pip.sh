#!/bin/bash

set -ex

cd /opt/stable-diffusion/stable-diffusion-webui
source venv/bin/activate

pip install torch torchvision
pip install git+https://github.com/TencentARC/GFPGAN.git@8d2447a2d918f8eba5a4a01463fd48e45126a379
pip install git+https://github.com/openai/CLIP.git@d50d76daa670286dd6cacf3bcd80b5e4823fc8e1
