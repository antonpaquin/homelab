from typing import Dict, List


import pulumi_kubernetes as k8s


def simple_pvc(name: str, namespace: str, storage_request: str) -> k8s.core.v1.PersistentVolumeClaim:
    return k8s.core.v1.PersistentVolumeClaim(
        resource_name=f'kubernetes-persistentvolumeclaim-{namespace}-{name}',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
        ),
        spec=k8s.core.v1.PersistentVolumeClaimSpecArgs(
            access_modes=["ReadWriteOnce"],
            resources=k8s.core.v1.ResourceRequirementsArgs(
                requests={
                    'storage': storage_request,
                },
            ),
        ),
    )

def simple_configmap(name: str, namespace: str, contents: Dict[str, str]) -> k8s.core.v1.ConfigMap:
    return k8s.core.v1.ConfigMap(
        resource_name=f'kubernetes-configmap-{namespace}-{name}',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name=name,
            namespace=namespace,
        ),
        data=contents
    )

def simple_env_vars(data: Dict[str, str]) -> List[k8s.core.v1.EnvVarArgs]:
    res = []
    for k, v in data.items():
        res.append(k8s.core.v1.EnvVarArgs(name=k, value=v))
    return res


def pvc_volume(name: str, pvc: k8s.core.v1.PersistentVolumeClaim) -> k8s.core.v1.VolumeArgs:
    return k8s.core.v1.VolumeArgs(
        name=name,
        persistent_volume_claim=k8s.core.v1.PersistentVolumeClaimVolumeSourceArgs(
            claim_name=pvc.metadata['name'],
        )
    )

def config_map_volume(name: str, cm: k8s.core.v1.ConfigMap) -> k8s.core.v1.VolumeArgs:
    return k8s.core.v1.VolumeArgs(
        name=name,
        config_map=k8s.core.v1.ConfigMapVolumeSourceArgs(
            name=cm.metadata['name'],
        ),
    )
