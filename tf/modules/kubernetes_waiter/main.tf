variable "kind" {
  type = string
}
variable "namespace" {
  type = string
  default = "default"
}
variable "name" {
  type = string
}

locals {
  script = "while ! kubectl get -n ${var.namespace} ${var.kind}/${var.name}; do sleep 1; done"
}

resource "null_resource" "wait-cmd" {
  triggers = {
    script = local.script
  }
  provisioner "local-exec" {
    command = local.script
  }
}
