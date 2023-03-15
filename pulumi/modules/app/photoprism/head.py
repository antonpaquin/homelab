import pulumi_kubernetes as k8s

from modules.lib.config_types import InitDB


class PhotoprismInstallation:
    initdb: InitDB
    secret: k8s.core.v1.Secret
    configmap: k8s.core.v1.ConfigMap
    sts: k8s.apps.v1.StatefulSet
    service: k8s.core.v1.Service

    def __init__(
        self,
        initdb: InitDB,
        secret: k8s.core.v1.Secret,
        configmap: k8s.core.v1.ConfigMap,
        sts: k8s.apps.v1.StatefulSet,
        service: k8s.core.v1.Service,
    ) -> None:
        self.initdb = initdb
        self.secret = secret
        self.configmap = configmap
        self.sts = sts
        self.service = service

