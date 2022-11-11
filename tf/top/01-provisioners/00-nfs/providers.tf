terraform {
  required_providers {
    kubernetes = {
      version = "2.2.0"
    }
    random = {
      version = "3.1.0"
    }
  }
}

provider "kubernetes" {
  config_path = "/home/anton/.kube/config"
}

provider "helm" {
  kubernetes {
    config_path = "/home/anton/.kube/config"
  }
}
