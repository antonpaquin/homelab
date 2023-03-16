from typing import List

import pulumi
import pulumi_kubernetes as k8s


class NginxPortSpec:
    name: str
    proto: str
    port: int

    def __init__(self, name: str, proto: str, port: int) -> None:
        self.name = name
        self.proto = proto
        self.port = port


class NginxInstallation(pulumi.ComponentResource):
    namespace: k8s.core.v1.Namespace
    service_account: k8s.core.v1.ServiceAccount
    config_map: k8s.core.v1.ConfigMap
    cluster_role: k8s.rbac.v1.ClusterRole
    cluster_role_binding: k8s.rbac.v1.ClusterRoleBinding
    role: k8s.rbac.v1.Role
    role_binding: k8s.rbac.v1.RoleBinding
    deployment: k8s.apps.v1.Deployment
    service: k8s.core.v1.Service
    ingress_class: k8s.networking.v1.IngressClass

    def __init__(
        self,
        resource_name: str,
        ports: List[NginxPortSpec] | None = None,
        opts: pulumi.ResourceOptions | None = None,
    ) -> None:
        super().__init__('anton:k8s_infra:NginxInstallation', resource_name, None, opts)

        if ports is None:
            ports = [
                NginxPortSpec(name='http', proto='TCP', port=80),
                NginxPortSpec(name='https', proto='TCP', port=443),
            ]

        _full_labels = {
            "app.kubernetes.io/component": "controller",
            "app.kubernetes.io/instance": "ingress-nginx",
            "app.kubernetes.io/name": "ingress-nginx",
            "app.kubernetes.io/part-of": "ingress-nginx",
            "app.kubernetes.io/version": "1.4.0",
        }

        _labels_ncomponent = _full_labels.copy()
        _labels_ncomponent.pop("app.kubernetes.io/component")

        _labels_selector = _full_labels.copy()
        _labels_selector.pop("app.kubernetes.io/version")
        _labels_selector.pop("app.kubernetes.io/part-of")

        self.namespace = k8s.core.v1.Namespace(
            resource_name=f'{resource_name}:namespace',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name='ingress-nginx',
                labels={
                    "app.kubernetes.io/instance": "ingress-nginx",
                    "app.kubernetes.io/name": "ingress-nginx",
                }
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.service_account = k8s.core.v1.ServiceAccount(
            resource_name=f'{resource_name}:serviceaccount',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name='ingress-nginx',
                namespace=self.namespace.metadata["name"],
                labels=_full_labels,
            ),
            automount_service_account_token=True,
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.namespace],
            ),
        )

        self.config_map = k8s.core.v1.ConfigMap(
            resource_name=f'{resource_name}:configmap',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="ingress-nginx-controller",
                namespace=self.namespace.metadata["name"],
                labels=_full_labels,
            ),
            data={
                "allow-snippet-annotations": "true",
                "hsts": "false",
            },
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.namespace],
            ),
        )

        self.cluster_role = k8s.rbac.v1.ClusterRole(
            resource_name=f"{resource_name}:clusterrole",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="ingress-nginx",
                labels=_labels_ncomponent,
            ),
            rules=[
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["list", "watch"],
                    api_groups=[""],
                    resources=["configmaps", "endpoints", "nodes", "pods", "secrets", "namespaces"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["list", "watch"],
                    api_groups=["coordination.k8s.io"],
                    resources=["leases"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get"],
                    api_groups=[""],
                    resources=["nodes"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get", "list", "watch"],
                    api_groups=[""],
                    resources=["services"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get", "list", "watch"],
                    api_groups=["networking.k8s.io"],
                    resources=["ingresses"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["create", "patch"],
                    api_groups=[""],
                    resources=["events"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["update"],
                    api_groups=["networking.k8s.io"],
                    resources=["ingresses/status"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get", "list", "watch"],
                    api_groups=["networking.k8s.io"],
                    resources=["ingressclasses"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get", "list", "watch"],
                    api_groups=["discovery.k8s.io"],
                    resources=["endpointslices"],
                ),
            ],
            opts=pulumi.ResourceOptions(
                parent=self,
            )
        )

        self.cluster_role_binding = k8s.rbac.v1.ClusterRoleBinding(
            resource_name=f'{resource_name}:clusterrolebinding',
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name='ingress-nginx',
                labels=_labels_ncomponent,
            ),
            subjects=[
                k8s.rbac.v1.SubjectArgs(
                    kind='ServiceAccount',
                    name=self.service_account.metadata["name"],
                    namespace=self.service_account.metadata["namespace"],
                ),
            ],
            role_ref=k8s.rbac.v1.RoleRefArgs(
                api_group="rbac.authorization.k8s.io",
                kind="ClusterRole",
                name=self.cluster_role.metadata["name"],
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.cluster_role, self.service_account],
            ),
        )

        self.role = k8s.rbac.v1.Role(
            resource_name=f"{resource_name}:role",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="ingress-nginx",
                namespace=self.namespace.metadata["name"],
                labels=_full_labels,
            ),
            rules=[
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get"],
                    api_groups=[""],
                    resources=["namespaces"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get", "list", "watch"],
                    api_groups=[""],
                    resources=["configmaps", "pods", "secrets", "endpoints"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get", "list", "watch"],
                    api_groups=[""],
                    resources=["services"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get", "list", "watch"],
                    api_groups=["networking.k8s.io"],
                    resources=["ingresses"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["update"],
                    api_groups=["networking.k8s.io"],
                    resources=["ingresses/status"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get", "list", "watch"],
                    api_groups=["networking.k8s.io"],
                    resources=["ingressclasses"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get", "update"],
                    api_groups=[""],
                    resources=["configmaps"],
                    resource_names=["ingress-controller-leader-nginx"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["create"],
                    api_groups=[""],
                    resources=["configmaps"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["get", "update"],
                    api_groups=["coordination.k8s.io"],
                    resources=["leases"],
                    resource_names=["ingress-controller-leader"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["create"],
                    api_groups=["coordination.k8s.io"],
                    resources=["leases"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["create", "patch"],
                    api_groups=[""],
                    resources=["events"],
                ),
                k8s.rbac.v1.PolicyRuleArgs(
                    verbs=["list", "watch", "get"],
                    api_groups=["discovery.k8s.io"],
                    resources=["endpointslices"],
                ),
            ],
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.namespace]
            ),
        )

        self.role_binding = k8s.rbac.v1.RoleBinding(
            resource_name=f"{resource_name}:rolebinding",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="ingress-nginx",
                namespace=self.namespace.metadata["name"],
                labels=_full_labels,
            ),
            subjects=[
                k8s.rbac.v1.SubjectArgs(
                    kind="ServiceAccount",
                    name=self.service_account.metadata["name"],
                    namespace=self.namespace.metadata["name"],
                )
            ],
            role_ref=k8s.rbac.v1.RoleRefArgs(
                api_group="rbac.authorization.k8s.io",
                kind="Role",
                name=self.role.metadata["name"],
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.role, self.service_account, self.namespace],
            ),
        )

        self.deployment = k8s.apps.v1.Deployment(
            resource_name=f"{resource_name}:deployment",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="ingress-nginx-controller",
                namespace=self.namespace.metadata["name"],
                labels=_full_labels,
            ),
            spec=k8s.apps.v1.DeploymentSpecArgs(
                selector=k8s.meta.v1.LabelSelectorArgs(
                    match_labels=_labels_selector,
                ),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(
                        labels=_labels_selector
                    ),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name='controller',
                                image="registry.k8s.io/ingress-nginx/controller:v1.4.0@sha256:34ee929b111ffc7aa426ffd409af44da48e5a0eea1eb2207994d9e0c0882d143",
                                args=[
                                    "/nginx-ingress-controller",
                                    "--publish-service=$(POD_NAMESPACE)/ingress-nginx-controller",
                                    "--election-id=ingress-controller-leader",
                                    "--controller-class=k8s.io/ingress-nginx",
                                    "--ingress-class=nginx",
                                    "--configmap=$(POD_NAMESPACE)/ingress-nginx-controller",
                                ],
                                ports=[
                                    k8s.core.v1.ContainerPortArgs(
                                        name=port.name,
                                        container_port=port.port,
                                        protocol=port.proto,
                                    )
                                    for port in ports
                                ] + [
                                    k8s.core.v1.ContainerPortArgs(
                                        name='webhook',
                                        container_port=8443,
                                        protocol="TCP"
                                    )
                                ],
                                env=[
                                    k8s.core.v1.EnvVarArgs(
                                        name='POD_NAME',
                                        value_from=k8s.core.v1.EnvVarSourceArgs(
                                            field_ref=k8s.core.v1.ObjectFieldSelectorArgs(
                                                field_path='metadata.name',
                                            ),
                                        )
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name='POD_NAMESPACE',
                                        value_from=k8s.core.v1.EnvVarSourceArgs(
                                            field_ref=k8s.core.v1.ObjectFieldSelectorArgs(
                                                field_path='metadata.namespace',
                                            ),
                                        )
                                    ),
                                    k8s.core.v1.EnvVarArgs(
                                        name='LD_PRELOAD',
                                        value="/usr/local/lib/libmimalloc.so",
                                    ),
                                ],
                                resources=k8s.core.v1.ResourceRequirementsArgs(
                                    requests={
                                        'cpu': '100m',
                                        'memory': '90Mi',
                                    },
                                ),
                                liveness_probe=k8s.core.v1.ProbeArgs(
                                    http_get=k8s.core.v1.HTTPGetActionArgs(
                                        path="/healthz",
                                        port=10254,
                                        scheme="HTTP",
                                    ),
                                    initial_delay_seconds=10,
                                    timeout_seconds=1,
                                    period_seconds=10,
                                    success_threshold=1,
                                    failure_threshold=5,
                                ),
                                readiness_probe=k8s.core.v1.ProbeArgs(
                                    http_get=k8s.core.v1.HTTPGetActionArgs(
                                        path="/healthz",
                                        port=10254,
                                        scheme="HTTP",
                                    ),
                                    initial_delay_seconds=10,
                                    timeout_seconds=1,
                                    period_seconds=10,
                                    success_threshold=1,
                                    failure_threshold=3,
                                ),
                                lifecycle=k8s.core.v1.LifecycleArgs(
                                    pre_stop=k8s.core.v1.LifecycleHandlerArgs(
                                        exec_=k8s.core.v1.ExecActionArgs(
                                            command=["/wait-shutdown"],
                                        ),
                                    ),
                                ),
                                image_pull_policy="IfNotPresent",
                                security_context=k8s.core.v1.SecurityContextArgs(
                                    capabilities=k8s.core.v1.CapabilitiesArgs(
                                        add=["NET_BIND_SERVICE"],
                                        drop=["ALL"],
                                    ),
                                    run_as_user=101,
                                    allow_privilege_escalation=True,
                                ),
                            ),
                        ],
                        termination_grace_period_seconds=300,
                        dns_policy="ClusterFirst",
                        node_selector={
                            'kubernetes.io/os': 'linux',
                        },
                        service_account_name=self.service_account.metadata['name'],
                    ),
                ),
                min_ready_seconds=0,
                revision_history_limit=10,
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.service_account, self.namespace],
            ),
        )

        self.service = k8s.core.v1.Service(
            resource_name=f"{resource_name}:service",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="ingress-nginx-controller",
                namespace=self.namespace.metadata["name"],
                labels=_full_labels,
            ),
            spec=k8s.core.v1.ServiceSpecArgs(
                external_traffic_policy="Local",
                ip_families=["IPv4"],
                ip_family_policy="SingleStack",
                ports=[
                    k8s.core.v1.ServicePortArgs(
                        name=p.name,
                        protocol=p.proto,
                        port=p.port,
                        target_port=p.name,
                        node_port=p.port,
                    )
                    for p in ports
                ],
                selector=_labels_selector,
                type='NodePort',
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deployment],
            ),
        )

        self.ingress_class = k8s.networking.v1.IngressClass(
            resource_name=f"{resource_name}:ingress-class",
            metadata=k8s.meta.v1.ObjectMetaArgs(
                name="nginx",
                labels=_full_labels,
            ),
            spec=k8s.networking.v1.IngressClassSpecArgs(
                controller="k8s.io/ingress-nginx"
            ),
            opts=pulumi.ResourceOptions(
                parent=self,
                depends_on=[self.deployment],
            ),
        )
