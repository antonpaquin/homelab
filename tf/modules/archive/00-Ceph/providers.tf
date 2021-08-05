terraform {
  required_providers {
    kubernetes = {
      version = "2.2.0"
    }
    kubernetes-alpha = {
      version = "0.4.1"
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

provider "kubernetes-alpha" {
  config_path = "/home/anton/.kube/config"
}
