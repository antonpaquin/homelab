all: build push

img:
	./authfail_img.sh

build: img
	docker build . -t antonpaquin/misc:authproxy

push:
	docker push antonpaquin/misc:authproxy
