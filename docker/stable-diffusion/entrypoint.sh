#! /bin/bash

cd /workspace/stable-diffusion-webui/

echo "unpacking models via symlink"
for f in /models/Stable-diffusion/*; do 
    ln -s $f /workspace/stable-diffusion-webui/models/Stable-diffusion/$(basename $f)
done

mkdir -p /root/.cache/huggingface/transformers
for f in /models/transformers/*; do 
    ln -s $f /root/.cache/huggingface/transformers/$(basename $f)
done

python launch.py "$@"