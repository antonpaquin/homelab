locals {
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
        url: "http://jellyfin.${var.domain}/Users/authenticatebyname"
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
        client-script: file("../modules/app_infra/authproxy/app/auth/jellyfin.js")
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
        url: "http://deluge.${var.domain}/json",
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

  domain_ceph = {
    # TODO: ceph actually supports saml.
    # How is saml supposed to work? What do I need to do?
    # weird hack is fine enough for now but eventually it would be cool to use the proper method where it's supported
    domain = "ceph-dashboard.${var.domain}"
    role = "ceph"
    auth = {
      type = "request"
      request = {
        method = "POST"
        url = "http://ceph-dashboard.${var.domain}/api/auth"
        headers = {
          accept: "application/vnd.ceph.api.v1.0+json"
          content-type = "application/json"
        }
        body = jsonencode({
          username = "admin"
          password = "cirno9ball"
        })
      }
      response = {
        set-cookie = true
        client-script = "localStorage.setItem(\"dashboard_username\", \"admin\"); window.location.replace(authproxy_rd);"
      }
    }
  }

  domain_grafana = {
    domain = "grafana.${var.domain}"
    role = "grafana"
    auth = {
      type = "request"
      request = {
        method = "POST"
        url = "http://grafana.${var.domain}/login"
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
        url = "http://komga.${var.domain}/api/v1/users/me"
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
        url = "http://photoprism.${var.domain}/api/v1/session"
        headers = {
          content-type = "application/json"
        }
        body = jsonencode({
          username = "admin"
          password = "cirno9ball"
        })
      }
      response = {
        client-script = file("../../modules/app_infra/authproxy/app/auth/photoprism.js")
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
    local.domain_ceph,
    local.domain_deluge,
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