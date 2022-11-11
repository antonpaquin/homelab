locals {
  users = {
    anton: {
      first_name: "Anton"
      last_name: "Paquin"
      email: "test@antonpaqu.in"
      groups: ["admin", "default"]
    },
    davos: {
      first_name: "Davos"
      last_name: "Paquin"
      email: "test@email.tld"
      groups: ["randos"]
    }
    mom: {
      first_name: "Aimee"
      last_name: "Paquin"
      email: "aimee@tuko.com"
      groups: ["mom"]
    }
    nadia: {
      first_name: "Nadia"
      last_name: "Paquin"
      email: "nadiampaquin@gmail.com"
      groups: ["nadia"]
    }
  }

  group_roles = {
    admin: [
      "ceph",
      "filebrowser",
      "jellyfin-admin",
      "logserv",
      "stable-diffusion"
    ],
    default: [
      "deluge",
      "filebrowser",
      "grafana",
      "grocy",
      "hardlinker",
      "komga",
      "metube",
      "photoprism",
      "prometheus",
      "sonarr",
      "tandoor",
    ],
    randos: [
      "komga",
      "metube"
    ]
    mom: ["grocy"]
    nadia: ["grocy"]
  }

  clients = {
    "authproxy-oidc": {
      redirect_uris: ["https://authproxy.antonpaqu.in/auth"]
    },
    "authproxy-ceph-oidc": {
      redirect_uris: ["https://authproxy-ceph.antonpaqu.in/auth"]
    },
    "matrix-synapse": {
      redirect_uris: ["https://matrix-synapse.antonpaqu.in/_synapse/client/oidc/callback"]
    }
  }
}

locals {
  groups = toset(flatten([
    [for _, v in local.users: v.groups],
    [for k, v in local.group_roles: k],
  ]))
  group_users = {
    for group in local.groups:
    group => [for user, v in local.users: user if contains(v.groups, group)]
  }

  roles = toset(flatten([for _, v in local.group_roles: v]))
}

resource "keycloak_realm" "default" {
  realm = "default"
  enabled = "true"
  default_signature_algorithm = "RS256"
  ssl_required = "none"  # todo fix
}

resource "keycloak_user" "user" {
  for_each = local.users
  realm_id = keycloak_realm.default.id
  username = each.key
  enabled = true

  email = each.value.email
  first_name = each.value.first_name
  last_name = each.value.last_name
}

resource "keycloak_group" "group" {
  for_each = local.groups
  realm_id = keycloak_realm.default.id
  name = each.value
}

resource "keycloak_group_memberships" "group_memberships" {
  for_each = local.groups
  realm_id = keycloak_realm.default.id
  group_id = keycloak_group.group[each.value].id
  members = lookup(local.group_users, each.value, [])
}

resource "keycloak_role" "role" {
  for_each = local.roles
  realm_id = keycloak_realm.default.id
  name = each.value
}

resource "keycloak_group_roles" "group_roles" {
  for_each = local.groups
  realm_id = keycloak_realm.default.id
  group_id = keycloak_group.group[each.value].id
  role_ids = [
    for role in local.group_roles[each.value]:
    keycloak_role.role[role].id
  ]
}

resource "keycloak_openid_client" "openid_client" {
  for_each = local.clients
  realm_id = keycloak_realm.default.id
  client_id = each.key
  name = each.key
  enabled = true
  access_type = "CONFIDENTIAL"
  valid_redirect_uris = each.value.redirect_uris
  login_theme = "keycloak"
  implicit_flow_enabled = true
  standard_flow_enabled = true
  direct_access_grants_enabled = true
  full_scope_allowed = true
}

resource "keycloak_openid_client_scope" "groups" {
  realm_id = keycloak_realm.default.id
  name = "groups"
  description = "When requested, this scope will map a user's group memberships to a claim"
  include_in_token_scope = true
}

resource "keycloak_openid_client_default_scopes" "client_default_scopes" {
  for_each = local.clients
  realm_id = keycloak_realm.default.id
  client_id = keycloak_openid_client.openid_client[each.key].id

  default_scopes = [
    "email",
    "profile",
    "roles",
    "web-origins",
    keycloak_openid_client_scope.groups.name,
  ]
}


resource "keycloak_openid_user_realm_role_protocol_mapper" "user_realm_role_mapper" {
  for_each = local.clients
  realm_id = keycloak_realm.default.id
  client_id = keycloak_openid_client.openid_client[each.key].id
  name = "${each.key}-role-mapper"

  claim_name = "resource_access.roles"
  claim_value_type = "String"
  multivalued = true
  add_to_id_token = true
}

# resource "keycloak_openid_client" "sso_client" {
#   realm_id = keycloak_realm.default.id
# }


# TODO: don't remember if I need to set up mappers here or if default is OK
