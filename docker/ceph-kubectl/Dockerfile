FROM docker.io/ceph/ceph:v16.2

RUN \
    curl \
        -L "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
        -o /bin/kubectl \
 && chmod 777 /bin/kubectl
