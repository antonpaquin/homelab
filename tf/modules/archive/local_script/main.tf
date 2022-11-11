variable "script" {
  type = string
}

variable "name" {
  type = string
}

locals {
  _script_fname = ".run/local_script_${var.name}.sh"
  _result_fname = ".run/local_script_${var.name}.out"
}

resource "local_file" "script_file" {
  filename = local._script_fname
  file_permission = "0777"
  content = var.script
}

resource "null_resource" "cmd-run" {
  depends_on = [local_file.script_file]
  triggers = {
    script = var.script
  }
  provisioner "local-exec" {
    command = "./\"${local_file.script_file.filename}\" | base64 > \"${local._result_fname}\""
  }
}

data "local_file" "cmd-out" {
  depends_on = [null_resource.cmd-run]
  filename = local._result_fname
}

output "result" {
  value = base64decode(trimspace(data.local_file.cmd-out.content))
}
