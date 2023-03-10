# locals {
#   ports = {
#     http: {
#       port: 80
#       name: "http"
#       proto: "TCP"
#     }
#     https: {
#       port: 443
#       name: "https"
#       proto: "TCP"
#     }
#   }
# }
# 
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


class NginxInstallation:
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


def create_nginx(ports: List[NginxPortSpec] | None = None) -> NginxInstallation:
    if ports is None:
        ports = [
            NginxPortSpec(name='http', proto='TCP', port=80),
            NginxPortSpec(name='https', proto='TCP', port=443),
        ]

    ns = k8s.core.v1.Namespace(
        resource_name='kubernetes-namespace-ingress-nginx',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name='ingress-nginx',
            labels={
                "app.kubernetes.io/instance": "ingress-nginx",
                "app.kubernetes.io/name": "ingress-nginx",
            }
        )
    )

    sa = k8s.core.v1.ServiceAccount(
        resource_name='kubernetes-serviceaccount-ingress-nginx',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name='ingress-nginx',
            namespace=ns.metadata["name"],
            labels={
                "app.kubernetes.io/component": "controller",
                "app.kubernetes.io/instance": "ingress-nginx",
                "app.kubernetes.io/name": "ingress-nginx",
                "app.kubernetes.io/part-of": "ingress-nginx",
                "app.kubernetes.io/version": "1.4.0",
            },
        ),
        automount_service_account_token=True,
    )

    cm = k8s.core.v1.ConfigMap(
        resource_name='kubernetes-configmap-ingress-nginx-controller',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="ingress-nginx-controller",
            namespace=ns.metadata["name"],
            labels={
                "app.kubernetes.io/component": "controller",
                "app.kubernetes.io/instance": "ingress-nginx",
                "app.kubernetes.io/name": "ingress-nginx",
                "app.kubernetes.io/part-of": "ingress-nginx",
                "app.kubernetes.io/version": "1.4.0",
            }
        ),
        data={
            "allow-snippet-annotations": "true",
            "hsts": "false",
        }
    )

    cr = k8s.rbac.v1.ClusterRole(
        resource_name="kubernetes-clusterrole-ingress-nginx",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="ingress-nginx",
            labels={
                "app.kubernetes.io/instance": "ingress-nginx",
                "app.kubernetes.io/name": "ingress-nginx",
                "app.kubernetes.io/version": "1.4.0",
                "app.kubernetes.io/part-of": "ingress-nginx",
            }
        ),
        rules=[
            k8s.rbac.v1.PolicyRuleArgs(
                verbs=["list", "watch"],
                api_groups=[""],
                resources=["leases"],
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
        ]
    )

    crb = k8s.rbac.v1.ClusterRoleBinding(
        resource_name='kubernetes-clusterrolebinding-ingress-nginx',
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name='ingress-nginx',
            labels={
                "app.kubernetes.io/instance": "ingress-nginx",
                "app.kubernetes.io/name": "ingress-nginx",
                "app.kubernetes.io/version": "1.4.0",
                "app.kubernetes.io/part-of": "ingress-nginx",
            }
        ),
        subjects=[
            k8s.rbac.v1.SubjectArgs(
                kind='ServiceAccount',
                name=sa.metadata["name"],
                namespace=sa.metadata["namespace"],
            ),
        ],
        role_ref=k8s.rbac.v1.RoleRefArgs(
            api_group="rbac.authorization.k8s.io",
            kind="ClusterRole",
            name=cr.metadata["name"],
        )
    )

    role = k8s.rbac.v1.Role(
        resource_name="kubernetes-role-ingress-nginx",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="ingress-nginx",
            namespace=ns.metadata["name"],
            labels={
                "app.kubernetes.iocomponent": "controller",
                "app.kubernetes.io/instance": "ingress-nginx",
                "app.kubernetes.io/name": "ingress-nginx",
                "app.kubernetes.io/version": "1.4.0",
                "app.kubernetes.io/part-of": "ingress-nginx",
            },
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
        ]
    )

    rb = k8s.rbac.v1.RoleBinding(
        resource_name="kubernetes-rolebinding-ingress-nginx",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="ingress-nginx",
            namespace=ns.metadata["name"],
            labels={
                "app.kubernetes.io/component": "controller",
                "app.kubernetes.io/instance": "ingress-nginx",
                "app.kubernetes.io/name": "ingress-nginx",
                "app.kubernetes.io/version": "1.4.0",
                "app.kubernetes.io/part-of": "ingress-nginx",
            }
        ),
        subjects=[
            k8s.rbac.v1.SubjectArgs(
                kind="ServiceAccount",
                name=sa.metadata["name"],
                namespace=ns.metadata["name"],
            )
        ],
        role_ref=k8s.rbac.v1.RoleRefArgs(
            api_group="rbac.authorization.k8s.io",
            kind="Role",
            name=role.metadata["name"],
        ),
    )

    service = k8s.core.v1.Service(
        resource_name="kubernetes-service-ingress-controller-nginx",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="ingress-nginx-controller",
            namespace=ns.metadata["name"],
            labels={
                "app.kubernetes.io/component": "controller",
                "app.kubernetes.io/instance": "ingress-nginx",
                "app.kubernetes.io/name": "ingress-nginx",
                "app.kubernetes.io/version": "1.4.0",
                "app.kubernetes.io/part-of": "ingress-nginx",
            }
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
            selector={
                "app.kubernetes.io/component": "controller",
                "app.kubernetes.io/instance": "ingress-nginx",
                "app.kubernetes.io/name": "ingress-nginx",
            },
            type='NodePort',
        ),
    )

    deployment = k8s.apps.v1.Deployment(
        resource_name="kubernetes-deployment-ingress-nginx-controller",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="ingress-nginx-controller",
            namespace=ns.metadata["name"],
            labels={
                "app.kubernetes.io/component": "controller",
                "app.kubernetes.io/instance": "ingress-nginx",
                "app.kubernetes.io/name": "ingress-nginx",
                "app.kubernetes.io/version": "1.4.0",
                "app.kubernetes.io/part-of": "ingress-nginx",
            },
        ),
        spec=k8s.apps.v1.DeploymentSpecArgs(
            selector=k8s.meta.v1.LabelSelectorArgs(
                match_labels={
                  "app.kubernetes.io/component": "controller",
                  "app.kubernetes.io/instance": "ingress-nginx",
                  "app.kubernetes.io/name": "ingress-nginx",
                },
            ),
            template=k8s.core.v1.PodTemplateSpecArgs(
                metadata=k8s.meta.v1.ObjectMetaArgs(
                    labels={
                        "app.kubernetes.io/component": "controller",
                        "app.kubernetes.io/instance": "ingress-nginx",
                        "app.kubernetes.io/name": "ingress-nginx",
                    }
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
                    service_account_name=sa.metadata['name'],
                ),
            ),
            min_ready_seconds=0,
            revision_history_limit=10,
        ),
    )

    ingress_class = k8s.networking.v1.IngressClass(
        resource_name="kubernetes-ingressclass-nginx",
        metadata=k8s.meta.v1.ObjectMetaArgs(
            name="nginx",
            labels={
                "app.kubernetes.io/component": "controller",
                "app.kubernetes.io/instance": "ingress-nginx",
                "app.kubernetes.io/name": "ingress-nginx",
                "app.kubernetes.io/part-of": "ingress-nginx",
                "app.kubernetes.io/version": "1.4.0",
            },
        ),
        spec=k8s.networking.v1.IngressClassSpecArgs(
            controller="k8s.io/ingress-nginx"
        )
    )

    return NginxInstallation(
        namespace=ns,
        service_account=sa,
        config_map=cm,
        cluster_role=cr,
        cluster_role_binding=crb,
        role=role,
        role_binding=rb,
        service=service,
        deployment=deployment,
        ingress_class=ingress_class,
    )
