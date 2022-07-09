terraform {
  required_providers {
    keycloak = {
      source = "mrparkers/keycloak"
      version = ">= 3.6.0"
    }
  }
}

# todo: bootstrap ???
locals {
  secret = yamldecode(file("../../secret.yaml"))
  domain = "antonpaqu.in"
}

provider "keycloak" {
  url = "http://keycloak.${local.domain}"
  client_id = "admin-cli"
  username = "admin"
  password = local.secret["keycloak"]["admin"]
}