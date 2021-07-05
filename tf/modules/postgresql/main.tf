resource "helm_release" "postgres" {
  repository = "https://charts.bitnami.com/bitnami"
  chart = "postgresql"
  name = "postgres"

  values = [yamlencode({
    securityContext: {
      enabled = true
      fsGroup = 1000
    }
    containerSecurityContext: {
      enabled = true
      runAsUser = 1000
    }

  })]
}