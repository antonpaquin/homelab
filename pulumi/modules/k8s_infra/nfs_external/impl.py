import pulumi
import pulumi_kubernetes as k8s


class ExternalNfs(pulumi.ComponentResource):
    service_account: k8s.core.v1.ServiceAccount
    deploy: k8s.apps.v1.Deployment
    cluster_role: k8s.rbac.v1.ClusterRole
    cluster_role_binding: k8s.rbac.v1.ClusterRoleBinding
    role: k8s.rbac.v1.Role
    role_binding: k8s.rbac.v1.RoleBinding
    storage_class: k8s.storage.v1.StorageClass

    def __init__(
        self,
        resource_name: str,
        name: str,
        storage_class_name: str,
        storage_node_ip: str,
        pvc_storage_path: str,
        namespace: str | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__('anton:k8s_infra:ExternalNfs', resource_name, None, opts)

        if namespace is None:
            namespace = 'kube-system'

        _labels = {'app': 'nfs-subdir-external-provisioner'}

        self.service_account = k8s.core.v1.ServiceAccount(
            resource_name=f'{resource_name}:service-account',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
                labels=_labels,
            )
        )

        self.deploy = k8s.apps.v1.Deployment(
            resource_name=f'{resource_name}:deployment',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                namespace=namespace,
                labels=_labels,
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=1,
                strategy=k8s.apps.v1.DeploymentStrategyArgs(
                    type="Recreate",
                ),
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels=_labels),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(labels=_labels),
                    spec=k8s.core.v1.PodSpecArgs(
                        service_account_name=self.service_account.metadata['name'],
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
                                        value=storage_node_ip,
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
                                    server=storage_node_ip,
                                    path=pvc_storage_path
                                ),
                            ),
                        ]
                    )
                ),
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.service_account],
            ),
        )

        self.cluster_role = k8s.rbac.v1.ClusterRole(
            resource_name=f'{resource_name}:cluster-role',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels=_labels,
                name=f"{name}-runner",
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
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.cluster_role_binding = k8s.rbac.v1.ClusterRoleBinding(
            resource_name=f'{resource_name}:cluster-role-binding',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=name,
                labels=_labels,
            ),
            subjects=[
                k8s.rbac.v1.SubjectArgs(
                    kind="ServiceAccount",
                    name=self.service_account.metadata["name"],
                    namespace=namespace,
                )
            ],
            role_ref=k8s.rbac.v1.RoleRefArgs(
                kind="ClusterRole",
                name=self.cluster_role.metadata["name"],
                api_group="rbac.authorization.k8s.io",
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.cluster_role, self.service_account],
            ),
        )

        self.role = k8s.rbac.v1.Role(
            resource_name=f'{resource_name}:role',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=f"{name}-leader-locking",
                namespace=namespace,
                labels=_labels,
            ),
            rules=[
                k8s.rbac.v1.PolicyRuleArgs(
                    api_groups=[""],
                    resources=["endpoints"],
                    verbs=["get", "list", "watch", "create", "update", "patch"],
                )
            ],
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.role_binding = k8s.rbac.v1.RoleBinding(
            resource_name=f'{resource_name}:role-binding',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=f"{name}-leader-locking",
                namespace=namespace,
                labels=_labels,
            ),
            subjects=[
                k8s.rbac.v1.SubjectArgs(
                    kind="ServiceAccount",
                    name=self.service_account.metadata["name"],
                    namespace=namespace, # chart specifies default -- why?
                ),
            ],
            role_ref=k8s.rbac.v1.RoleRefArgs(
                kind="Role",
                name=self.role.metadata["name"],
                api_group="rbac.authorization.k8s.io",
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.role, self.service_account],
            ),
        )

        self.storage_class = k8s.storage.v1.StorageClass(
            resource_name=f'{resource_name}:storage-class',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name=storage_class_name,
                labels=_labels,
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
            },
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deploy],
            ),
        )
