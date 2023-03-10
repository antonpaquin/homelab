import pulumi_kubernetes as k8s

from .head import MariaDBInstallation


def create_mariadb(namespace: str, password: str, storage_size: str) -> MariaDBInstallation:
    # pulumi for mariadb via helm

    chart = k8s.helm.v3.Chart(
        "mariadb",
        k8s.helm.v3.ChartOpts(
            chart="mariadb",
            namespace=namespace,
            version="11.1.0",
            fetch_opts=k8s.helm.v3.FetchOpts(
                repo="https://charts.bitnami.com/bitnami"
            ),
            values={
                # Mysql needs the clusterDomain because
                "auth": {
                    "rootPassword": password,
                },
                "primary": {
                    "persistence": {
                        "size": storage_size,
                        "storageClass": "nfs-client",
                    },
                },
            },
        ),
    )

    return MariaDBInstallation(
        chart=chart,
        namespace=namespace,
        port=3306,
        service_name='mariadb',
        user='root',
        password=password,
    )
