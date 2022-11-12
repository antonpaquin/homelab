locals {
  namespace = "kube-system"
}

resource "kubernetes_labels" "gpu_node_labels" {
    # would be nice if I could also do taints this way, but alas terraform
    api_version = "v1"
    kind = "Node"
    metadata {
        name = "cirno"
    }
    labels = {
      "nvidia.com/gpu-enabled" = "true"
    }
}


resource "helm_release" "nvidia_device_plugin" {
    wait = false
    wait_for_jobs = false
    repository = "https://nvidia.github.io/k8s-device-plugin"
    chart = "nvidia-device-plugin"
    version = "0.12.3"

    name = "nvidia-device-plugin"
    namespace = local.namespace

    values = [yamlencode({
        nodeSelector: {
            "nvidia.com/gpu-enabled": "true"
        }
    })]
}