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

mkdir -p /root/.cache/torch/hub/checkpoints/
for f in /models/torch_checkpoints/*; do
    ln -s $f /root/.cache/torch/hub/checkpoints/$(basename $f)
done

mkdir -p /root/.cache/clip
for f in /models/clip/*; do
    ln -s $f /root/.cache/clip/$(basename $f)
done
model_base_caption_capfilt_large.pth .

python launch.py "$@"