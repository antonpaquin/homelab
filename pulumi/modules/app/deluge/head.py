import pulumi
import pulumi_kubernetes as k8s

from modules.lib.pulumi_model import PulumiModel


class DelugeInstallation(PulumiModel):
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

    def export(self, prefix: str):
        pulumi.export(f"{prefix}.config_pvc", self.config_pvc)
        pulumi.export(f"{prefix}.config_cm", self.config_cm)
        pulumi.export(f"{prefix}.deploy", self.deploy)
        pulumi.export(f"{prefix}.service", self.service)