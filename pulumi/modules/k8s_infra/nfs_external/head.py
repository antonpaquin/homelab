import pulumi
import pulumi_kubernetes as k8s

from modules.lib.pulumi_model import PulumiModel


class ExternalNfs(PulumiModel):
    storage_class: k8s.storage.v1.StorageClass
    service_account: k8s.core.v1.ServiceAccount
    deploy: k8s.apps.v1.Deployment
    cluster_role: k8s.rbac.v1.ClusterRole
    cluster_role_binding: k8s.rbac.v1.ClusterRoleBinding
    role: k8s.rbac.v1.Role
    role_binding: k8s.rbac.v1.RoleBinding

    def __init__(
        self,
        storage_class: k8s.storage.v1.StorageClass,
        service_account: k8s.core.v1.ServiceAccount,
        deploy: k8s.apps.v1.Deployment,
        cluster_role: k8s.rbac.v1.ClusterRole,
        cluster_role_binding: k8s.rbac.v1.ClusterRoleBinding,
        role: k8s.rbac.v1.Role,
        role_binding: k8s.rbac.v1.RoleBinding,
    ) -> None:
        super().__init__()
        self.storage_class = storage_class
        self.service_account = service_account
        self.deploy = deploy
        self.cluster_role = cluster_role
        self.cluster_role_binding = cluster_role_binding
        self.role = role
        self.role_binding = role_binding

    def export(self, prefix: str):
        pulumi.export(f"{prefix}.storage_class", self.storage_class)
        pulumi.export(f"{prefix}.service_account", self.service_account)
        pulumi.export(f"{prefix}.deploy", self.deploy)
        pulumi.export(f"{prefix}.cluster_role", self.cluster_role)
        pulumi.export(f"{prefix}.cluster_role_binding", self.cluster_role_binding)
        pulumi.export(f"{prefix}.role", self.role)
        pulumi.export(f"{prefix}.role_binding", self.role_binding)