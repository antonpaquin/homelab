import pulumi_kubernetes as k8s


class DelugeInstallation:
    config_pvc: k8s.core.v1.PersistentVolumeClaim
    config_cm: k8s.core.v1.ConfigMap
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service

    def __init__(
        self,
        config_pvc: k8s.core.v1.PersistentVolumeClaim,
        config_cm: k8s.core.v1.ConfigMap,
        deploy: k8s.apps.v1.Deployment,
        service: k8s.core.v1.Service,
    ) -> None:
        self.config_pvc = config_pvc
        self.config_cm = config_cm
        self.deploy = deploy
        self.service = service
