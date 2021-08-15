
locals {
  domain_filebrowser = {
    domain: "filebrowser.k8s.local",
    role: "filebrowser",
    auth: {}
  }

  domain_jellyfin_admin_js = {
    domain: "jellyfin.k8s.local",
    role: "jellyfin-admin",
    auth: {
      type: "request",
      request: {
        method: "POST",
        url: "http://jellyfin.k8s.local/Users/authenticatebyname"
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
        client-script: file("../../modules/authproxy/app/auth/jellyfin.js")
      }
    }
  }

  domain_deluge = {
    domain: "deluge.k8s.local",
    role: "deluge",
    auth: {
      type: "request",
      request: {
        method: "POST",
        url: "http://deluge.k8s.local/json",
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
    domain = "ceph-dashboard.k8s.local"
    role = "ceph"
    auth = {
      type = "request"
      request = {
        method = "POST"
        url = "http://ceph-dashboard.k8s.local/api/auth"
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
    domain = "grafana.k8s.local"
    role = "grafana"
    auth = {
      type = "request"
      request = {
        method = "POST"
        url = "http://grafana.k8s.local/login"
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

  domain_komga = {
    domain = "komga.k8s.local"
    role = "komga"
    auth = {
      type = "request"
      request = {
        method = "GET"
        url = "http://komga.k8s.local/api/v1/users/me"
        headers = {
          Authorization = "Basic ${base64encode("scratch@antonpaqu.in:cirno9ball")}"
        }
      }
      response = {
        set-cookie = true
      }
    }
  }

  domain_metube = {
    domain = "metube.k8s.local"
    role = "metube"
    auth = {}
  }

  domain_photoprism = {
    domain = "photoprism.k8s.local"
    role = "photoprism"
    auth = {
      type = "request"
      request = {
        method = "POST"
        url = "http://photoprism.k8s.local/api/v1/session"
        headers = {
          content-type = "application/json"
        }
        body = jsonencode({
          username = "admin"
          password = "cirno9ball"
        })
      }
      response = {
        client-script = file("../../modules/authproxy/app/auth/photoprism.js")
      }
    }
  }

  domain_prometheus = {
    domain = "prometheus.k8s.local"
    role = "prometheus"
    auth = {}
  }

  domain_sonarr = {
    domain = "sonarr.k8s.local"
    role = "sonarr"
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
    local.domain_jellyfin_admin_js,
    local.domain_komga,
    local.domain_metube,
    local.domain_photoprism,
    local.domain_prometheus,
    local.domain_sonarr,
  ]
}