import pulumi_kubernetes as k8s


class ExternalNfs:
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
