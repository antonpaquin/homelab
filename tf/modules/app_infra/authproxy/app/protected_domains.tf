locals {
  cluster_local = "default.svc.cluster.local"

  domain_filebrowser = {
    domain: "filebrowser.${var.domain}",
    role: "filebrowser",
    auth: {}
  }

  domain_jellyfin_admin_js = {
    domain: "jellyfin.${var.domain}",
    role: "jellyfin-admin",
    auth: {
      type: "request",
      request: {
        method: "POST",
        url: "http://jellyfin.${local.cluster_local}/Users/authenticatebyname"
        headers: {
          "X-Emby-Authorization": "MediaBrowser Client=\"Jellyfin Web\", Device=\"Firefox\", DeviceId=\"${base64encode("Mozilla/5.0 (X11; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0|1628227335649\ru")}\", Version=\"10.7.6\""
          "content-type": "application/json"
        }
        body: jsonencode({
          Username: "admin"
          Pw: "cirno9ball"
        })
      }
      response: {
        set-cookie: false
        client-script: file("../../../modules/app_infra/authproxy/app/auth/jellyfin.js")
      }
    }
  }

  domain_deluge = {
    domain: "deluge.${var.domain}",
    role: "deluge",
    auth: {
      type: "request",
      request: {
        method: "POST",
        url: "http://deluge.${local.cluster_local}/json",
        headers: {
          content-type: "application/json"
        },
        body: jsonencode({
          id: 0
          method: "auth.login"
          params: ["cirno9ball"]
        }),
      },
      response: {
        set-cookie: true
      }
    }
  }

  domain_distributed_diffusion = {
    domain = "distributed-diffusion.${var.domain}"
    role = "distributed-diffusion"
    auth = {}
  }

  domain_grafana = {
    domain = "grafana.${var.domain}"
    role = "grafana"
    auth = {
      type = "request"
      request = {
        method = "POST"
        url = "http://grafana.${local.cluster_local}/login"
        headers = {
          content-type = "application/json"
        }
        body = jsonencode({
          user = "admin"
          password = "cirno9ball"
        })
      }
      response = {
        set-cookie = true
      }
    }
  }

  domain_grocy = {
    domain = "grocy.${var.domain}"
    role = "grocy"
    auth = {}
  }

  domain_hardlinker = {
    domain = "hardlinker.${var.domain}"
    role = "hardlinker"
    auth = {}
  }

  domain_komga = {
    domain = "komga.${var.domain}"
    role = "komga"
    auth = {
      type = "request"
      request = {
        method = "GET"
        url = "http://komga.${local.cluster_local}/api/v1/users/me"
        headers = {
          Authorization = "Basic ${base64encode("scratch@antonpaqu.in:cirno9ball")}"
        }
      }
      response = {
        set-cookie = true
      }
    }
  }

  domain_logserv = {
    domain = "logserv.${var.domain}"
    role = "logserv"
    auth = {}
  }

  domain_metube = {
    domain = "metube.${var.domain}"
    role = "metube"
    auth = {}
  }

  domain_photoprism = {
    domain = "photoprism.${var.domain}"
    role = "photoprism"
    auth = {
      type = "request"
      request = {
        method = "POST"
        url = "http://photoprism.${local.cluster_local}/api/v1/session"
        headers = {
          content-type = "application/json"
        }
        body = jsonencode({
          username = "admin"
          password = "cirno9ball"
        })
      }
      response = {
        client-script = file("../../../modules/app_infra/authproxy/app/auth/photoprism.js")
      }
    }
  }

  domain_prometheus = {
    domain = "prometheus.${var.domain}"
    role = "prometheus"
    auth = {}
  }

  domain_sonarr = {
    domain = "sonarr.${var.domain}"
    role = "sonarr"
    auth = {}
  }

  domain_stable_diffusion = {
    domain = "stable-diffusion.${var.domain}"
    role = "stable-diffusion"
    auth = {}
  }

  domain_tandoor = {
    domain = "tandoor.${var.domain}"
    role = "tandoor"
    auth = {}
  }
}

locals {
  # OK if options are unused -- restrictions are imposed at the ingress level, not here.
  # "protected_ingress" is the gate, "protected-domains" are the available keys to the gates
  protected-domains = [
    local.domain_deluge,
    local.domain_distributed_diffusion,
    local.domain_filebrowser,
    local.domain_grafana,
    local.domain_grocy,
    local.domain_hardlinker,
    local.domain_jellyfin_admin_js,
    local.domain_komga,
    local.domain_logserv,
    local.domain_metube,
    local.domain_photoprism,
    local.domain_prometheus,
    local.domain_sonarr,
    local.domain_stable_diffusion,
    local.domain_tandoor,
  ]
}