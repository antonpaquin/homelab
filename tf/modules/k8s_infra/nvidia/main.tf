locals {
  namespace = "kube-system"
}


resource "helm_release" "nvidia_device_plugin" {
    wait = false
    repository = "https://nvidia.github.io/k8s-device-plugin"
    chart = "nvidia-device-plugin"
    version = "0.12.3"

    name = "nvidia-device-plugin"
    namespace = local.namespace

    values = []
}