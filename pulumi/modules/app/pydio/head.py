import pulumi_kubernetes as k8s


class PydioInstallation:
    deploy: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service
    pvc: k8s.core.v1.PersistentVolumeClaim

    def __init__(
        self,
        deploy: k8s.apps.v1.Deployment,
        service: k8s.core.v1.Service,
        pvc: k8s.core.v1.PersistentVolumeClaim,
    ) -> None:
        self.deploy = deploy
        self.service = service
        self.pvc = pvc