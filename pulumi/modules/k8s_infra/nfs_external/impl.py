import pulumi_kubernetes as k8s

from .head import ExternalNfs

def create_external_nfs(namespace: str, pvc_storage_path: str, node_ip: str) -> ExternalNfs:
    storage_class = k8s.storage.v1.StorageClass(
        resource_name='kubernetes-storageclass-nfs-subdir',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="nfs-client",
            labels={
                "app": "nfs-subdir-external-provisioner",
            },
            annotations={
                "storageclass.kubernetes.io/is-default-class": 'True',
            },
        ),
        provisioner="cluster.local/nfs-subdir-external-provisioner",
        allow_volume_expansion=True,
        reclaim_policy="Delete",
        volume_binding_mode="Immediate",
        parameters={
            "archiveOnDelete": "true",
        }
    )

    service_account = k8s.core.v1.ServiceAccount(
        resource_name="kubernetes-serviceaccount-nfs-subdir-external-provisioner",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="nfs-subdir-external-provisioner",
            namespace=namespace,
            labels={
                'app': "nfs-subdir-external-provisioner"
            }
        )
    )

    deploy = k8s.apps.v1.Deployment(
        resource_name='kubernetes-deployment-nfs-subdir-external-provisioner',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name='nfs-subdir-external-provisioner',
            namespace=namespace,
            labels={
                'app': "nfs-subdir-external-provisioner",
            },
        ),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            replicas=1,
            strategy=k8s.apps.v1.DeploymentStrategyArgs(
                type="Recreate",
            ),
            selector=k8s.meta.v1.LabelSelectorArgs(
                match_labels={
                    'app': "nfs-subdir-external-provisioner",
                },
            ),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    labels={
                        "app": "nfs-subdir-external-provisioner",
                    },
                ),
                spec=k8s.core.v1.PodSpecArgs(
                    service_account_name=service_account.metadata['name'],
                    containers=[
                        k8s.core.v1.ContainerArgs(
                            name="nfs-subdir-external-provisioner",
                            image="k8s.gcr.io/sig-storage/nfs-subdir-external-provisioner:v4.0.2",
                            image_pull_policy="IfNotPresent",
                            volume_mounts=[
                                k8s.core.v1.VolumeMountArgs(
                                    name="nfs-subdir-external-provisioner-root",
                                    mount_path="/persistentvolumes",
                                ),
                            ],
                            env=[
                                k8s.core.v1.EnvVarArgs(
                                    name='PROVISIONER_NAME',
                                    value="cluster.local/nfs-subdir-external-provisioner",
                                ),
                                k8s.core.v1.EnvVarArgs(
                                    name="NFS_SERVER",
                                    value=node_ip,
                                ),
                                k8s.core.v1.EnvVarArgs(
                                    name="NFS_PATH",
                                    value=pvc_storage_path,
                                ),
                            ]
                        ),
                    ],
                    volumes=[
                        k8s.core.v1.VolumeArgs(
                            name="nfs-subdir-external-provisioner-root",
                            nfs=k8s.core.v1.NFSVolumeSourceArgs(
                                server=node_ip,
                                path=pvc_storage_path
                            ),
                        ),
                    ]
                )
            ),
        ),
    )

    cluster_role = k8s.rbac.v1.ClusterRole(
        resource_name="kubernetes-clusterrole-nfs-subdir-external-provisioner-runner",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            labels={
                'app': "nfs-subdir-external-provisioner",
            },
            name="nfs-subdir-external-provisioner-runner",
        ),
        rules=[
            k8s.rbac.v1.PolicyRuleArgs(
                api_groups=[""],
                resources=["nodes"],
                verbs=["get", "list", "watch"],
            ),
            k8s.rbac.v1.PolicyRuleArgs(
                api_groups=[""],
                resources=["persistentvolumes"],
                verbs=["get", "list", "watch", "create", "delete"],
            ),
            k8s.rbac.v1.PolicyRuleArgs(
                api_groups=[""],
                resources=["persistentvolumeclaims"],
                verbs=["get", "list", "watch", "update"],
            ),
            k8s.rbac.v1.PolicyRuleArgs(
                api_groups=["storage.k8s.io"],
                resources=["storageclasses"],
                verbs=["get", "list", "watch"],
            ),
            k8s.rbac.v1.PolicyRuleArgs(
                api_groups=[""],
                resources=["events"],
                verbs=["create", "update", "patch"],
            ),
        ],
    )

    cluster_role_binding = k8s.rbac.v1.ClusterRoleBinding(
        resource_name="kubernetes-clusterrolebinding-run-nfs-subdir-external-provisioner",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="run-nfs-subdir-external-provisioner",
            labels={
                "app": "nfs-subdir-external-provisioner",
            },
        ),
        subjects=[
            k8s.rbac.v1.SubjectArgs(
                kind="ServiceAccount",
                name=service_account.metadata["name"],
                namespace=namespace,
            )
        ],
        role_ref=k8s.rbac.v1.RoleRefArgs(
            kind="ClusterRole",
            name=cluster_role.metadata["name"],
            api_group="rbac.authorization.k8s.io",
        ),
    )

    role = k8s.rbac.v1.Role(
        resource_name="kubernetes-role-leader-locking-nfs-subdir-external-provisioner",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="leader-locking-nfs-subdir-external-provisioner",
            namespace=namespace,
            labels={
                "app": "nfs-subdir-external-provisioner",
            },
        ),
        rules=[
            k8s.rbac.v1.PolicyRuleArgs(
                api_groups=[""],
                resources=["endpoints"],
                verbs=["get", "list", "watch", "create", "update", "patch"],
            )
        ]
    )

    role_binding = k8s.rbac.v1.RoleBinding(
        resource_name="kubernetes-rolebinding-leader-locking-nfs-subdir-external-provisioner",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="leader-locking-nfs-subdir-external-provisioner",
            namespace=namespace,
            labels={
                "app": "nfs-subdir-external-provisioner",
            }
        ),
        subjects=[
            k8s.rbac.v1.SubjectArgs(
                kind="ServiceAccount",
                name=service_account.metadata["name"],
                namespace=namespace, # chart specifies default -- why?,
            ),
        ],
        role_ref=k8s.rbac.v1.RoleRefArgs(
            kind="Role",
            name=role.metadata["name"],
            api_group="rbac.authorization.k8s.io",
        ),
    )

    return ExternalNfs(
        storage_class=storage_class,
        service_account=service_account,
        deploy=deploy,
        cluster_role=cluster_role,
        cluster_role_binding=cluster_role_binding,
        role=role,
        role_binding=role_binding,
    )
