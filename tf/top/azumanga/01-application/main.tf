locals {
  secret = yamldecode(file("../../../secret.yaml"))
  domain = "tuko.com"

  cluster = {
    yomi = {
      local-ip-address = "10.10.10.1"
    }
    chiyo = {
      local-ip-address = "10.10.10.2"
    }
    sakaki = {
      local-ip-address = "10.10.10.3"
    }
    osaka = {
      local-ip-address = "10.10.10.4"
    }
  }
}
