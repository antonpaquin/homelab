variable "command" {
  type = string
}

variable "image" {
  type = string
}

variable "name" {
  type = string
}

locals {
  _kctl_run_opts = join(" ", [
    "--image=${var.image}",
    "--wait=true",
    "--rm=true",
    "--attach=true",
    "--restart=Never",
    "--quiet=true",
  ])
  _result_fname = ".run/kubectl_cmd_${var.name}.out"
  _kctl_cmd = "kubectl run ${var.name} ${local._kctl_run_opts} -- ${var.command} | base64 > ${local._result_fname}"
}

resource "local_file" "output_dir" {
  filename = ".run/.tfkeep"
}

resource "null_resource" "cmd-run" {
  depends_on = [local_file.output_dir]
  triggers = {
    command = local._kctl_cmd
  }
  provisioner "local-exec" {
    command = local._kctl_cmd
  }
}

data "local_file" "cmd-out" {
  depends_on = [null_resource.cmd-run]
  filename = local._result_fname
}

output "result" {
  value = base64decode(trimspace(data.local_file.cmd-out.content))
}

