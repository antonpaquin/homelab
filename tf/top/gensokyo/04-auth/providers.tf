terraform {
  required_providers {
    keycloak = {
      source = "mrparkers/keycloak"
      version = ">= 3.9.1"
    }
  }
}

# todo: bootstrap ???
locals {
  secret = yamldecode(file("../../secret.yaml"))
  domain = "antonpaqu.in"
}

provider "keycloak" {
  url = "https://keycloak.${local.domain}"
  base_path = ""
  client_id = "admin-cli"
  username = "admin"
  password = local.secret["keycloak"]["admin"]
}