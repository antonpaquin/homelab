# do this to start the cluster
kubeadm init \
  --pod-network-cidr=10.244.0.0/16