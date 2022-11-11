TAG=antonpaquin/misc:stable-diffusion-webui

all: build push

build:
	docker build . -t $(TAG)

push:
	docker push $(TAG)

test:
	docker run \
		--rm \
		-v /home/anton/code/homelab/docker/stable-diffusion/models:/opt/stable-diffusion/stable-diffusion-webui/models \
		-v /home/anton/code/homelab/docker/stable-diffusion/models/transformers:/root/.cache/huggingface/transformers \
		-p 7860:7860 \
		$(TAG)

run-shell:
	docker run \
		--rm \
		-v /home/anton/code/homelab/docker/stable-diffusion/models:/opt/stable-diffusion/stable-diffusion-webui/models \
		-v /home/anton/code/homelab/docker/stable-diffusion/models/transformers:/root/.cache/huggingface/transformers \
		-p 7860:7860 \
		-it \
		--name stable-diffusion \
		--entrypoint=/bin/bash \
		$(TAG)

shell:
	docker exec -it stable-diffusion /bin/bash
