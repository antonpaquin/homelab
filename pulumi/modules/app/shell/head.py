import pulumi_kubernetes as k8s


class ShellInstallation:
    deployment: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service
    configmap: k8s.core.v1.ConfigMap
    persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim

    def __init__(
        self,
        deployment: k8s.apps.v1.Deployment,
        service: k8s.core.v1.Service,
        configmap: k8s.core.v1.ConfigMap,
        persistent_volume_claim: k8s.core.v1.PersistentVolumeClaim,
    ) -> None:
        self.deployment = deployment
        self.service = service
        self.configmap = configmap
        self.persistent_volume_claim = persistent_volume_claim