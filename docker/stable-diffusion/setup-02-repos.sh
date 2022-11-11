#! /bin/bash

set -ex

cd /opt/stable-diffusion/stable-diffusion-webui
mkdir repositories
cd repositories

git clone https://github.com/CompVis/stable-diffusion.git stable-diffusion
git -C stable-diffusion checkout 69ae4b35e0a0f6ee1af8bb9a5d0016ccb27e36dc

git clone https://github.com/CompVis/taming-transformers.git taming-transformers
git -C taming-transformers checkout 24268930bf1dce879235a7fddd0b2355b84d7ea6

git clone https://github.com/crowsonkb/k-diffusion.git k-diffusion
git -C k-diffusion checkout 1a0703dfb7d24d8806267c3e7ccc4caf67fd1331

git clone https://github.com/sczhou/CodeFormer.git CodeFormer
git -C CodeFormer checkout c5b4593074ba6214284d6acd5f1719b6c5d739af

git clone https://github.com/salesforce/BLIP.git BLIP
git -C BLIP checkout 48211a1594f1321b00f14c9f7a5b4813144b2fb9
