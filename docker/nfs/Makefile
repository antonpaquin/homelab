TAG=antonpaquin/misc:nfs-server

all: build push

build:
	docker build . -t $(TAG)

push:
	docker push $(TAG)
