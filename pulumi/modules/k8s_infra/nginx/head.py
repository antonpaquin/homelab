import pulumi
import pulumi_kubernetes as k8s


from modules.lib.pulumi_model import PulumiModel


class NginxPortSpec:
    name: str
    proto: str
    port: int

    def __init__(self, name: str, proto: str, port: int) -> None:
        self.name = name
        self.proto = proto
        self.port = port


class NginxInstallation(PulumiModel):
    namespace: k8s.core.v1.Namespace
    service_account: k8s.core.v1.ServiceAccount
    config_map: k8s.core.v1.ConfigMap
    cluster_role: k8s.rbac.v1.ClusterRole
    cluster_role_binding: k8s.rbac.v1.ClusterRoleBinding
    role: k8s.rbac.v1.Role
    role_binding: k8s.rbac.v1.RoleBinding
    service: k8s.core.v1.Service
    deployment: k8s.apps.v1.Deployment
    ingress_class: k8s.networking.v1.IngressClass

    def __init__(
        self,
        namespace: k8s.core.v1.Namespace,
        service_account: k8s.core.v1.ServiceAccount,
        config_map: k8s.core.v1.ConfigMap,
        cluster_role: k8s.rbac.v1.ClusterRole,
        cluster_role_binding: k8s.rbac.v1.ClusterRoleBinding,
        role: k8s.rbac.v1.Role,
        role_binding: k8s.rbac.v1.RoleBinding,
        service: k8s.core.v1.Service,
        deployment: k8s.apps.v1.Deployment,
        ingress_class: k8s.networking.v1.IngressClass,
    ) -> None:
        self.namespace = namespace
        self.service_account = service_account
        self.config_map = config_map
        self.cluster_role = cluster_role
        self.cluster_role_binding = cluster_role_binding
        self.role = role
        self.role_binding = role_binding
        self.service = service
        self.deployment = deployment
        self.ingress_class = ingress_class

    def export(self, prefix: str):
        pulumi.export(f"{prefix}.namespace", self.namespace)
        pulumi.export(f"{prefix}.service_account", self.service_account)
        pulumi.export(f"{prefix}.config_map", self.config_map)
        pulumi.export(f"{prefix}.cluster_role", self.cluster_role)
        pulumi.export(f"{prefix}.cluster_role_binding", self.cluster_role_binding)
        pulumi.export(f"{prefix}.role", self.role)
        pulumi.export(f"{prefix}.role_binding", self.role_binding)
        pulumi.export(f"{prefix}.service", self.service)
        pulumi.export(f"{prefix}.deployment", self.deployment)
        pulumi.export(f"{prefix}.ingress_class", self.ingress_class)