#! /bin/bash

set -ex

# Only needs to be used when applying for the first time, when there is no terraform state (or after a full terraform destroy).
# In most cases resetting and starting from scratch, it's fine to just apply without this

# See https://github.com/hashicorp/terraform-provider-kubernetes/issues/848
# TODO: fix
# terraform import module.coredns.kubernetes_service_account.coredns kube-system/coredns

terraform import module.coredns.kubernetes_service.kube_dns kube-system/kube-dns
terraform import module.coredns.kubernetes_deployment.coredns kube-system/coredns
terraform import module.coredns.kubernetes_config_map.coredns kube-system/coredns
terraform import module.coredns.kubernetes_cluster_role.system_coredns system:coredns
terraform import module.coredns.kubernetes_cluster_role_binding.system_coredns system:coredns
