#! /bin/bash

SRC_DIR="$(dirname "${BASH_SOURCE[0]}")"
cd "$SRC_DIR"

set -ex

kubeadm_init="$(
ssh chiyo <<EOF
    set -ex
    sudo kubeadm init '--pod-network-cidr=10.244.0.0/16'
EOF
)"
kubeadm_join="$(echo "$kubeadm_init" | grep -A2 "kubeadm join")"

echo $kubeadm_join

ssh sakaki <<EOF
  sudo $kubeadm_join
EOF

ssh chiyo <<EOF
    set -ex
    echo '*** kube-apiserver.yaml 2021-07-02 21:57:02.719492094 -0700
--- /etc/kubernetes/manifests/kube-apiserver.yaml       2021-07-02 21:57:33.909492078 -0700
***************
*** 39,44 ****
--- 39,45 ----
      - --service-account-key-file=/etc/kubernetes/pki/sa.pub
      - --service-account-signing-key-file=/etc/kubernetes/pki/sa.key
      - --service-cluster-ip-range=10.96.0.0/12
+     - --service-node-port-range=50-30000
      - --tls-cert-file=/etc/kubernetes/pki/apiserver.crt
      - --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
      image: k8s.gcr.io/kube-apiserver:v1.25.3' | sudo patch /etc/kubernetes/manifests/kube-apiserver.yaml
      sudo rm /etc/kubernetes/manifests/kube-apiserver.yaml.orig || true
EOF

kubeconfig="$(
ssh chiyo <<EOF
    set -ex
    sudo cat /etc/kubernetes/admin.conf
EOF
)"


echo "$kubeconfig" >> /home/anton/.kube/config
