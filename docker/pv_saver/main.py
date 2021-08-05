#! /usr/bin/env python

import argparse
from typing import Dict, List
import logging
import os
import time

import kubernetes
import yaml


PvName = str
FilePath = str
RawPvYaml = Dict
ReducedPvYaml = Dict

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

kubernetes.config.load_incluster_config()
kclient = kubernetes.client.CoreV1Api()
with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace') as in_ff:
    k_namespace = in_ff.read().strip()
k_sentinel_name = 'pv-saver-sentinel'

_storage_dir = None

_pv_strip_fields = {
    'status': None,
    'metadata': {
        'managedFields': None,
        'annotations': {
            'kubectl.kubernetes.io/last-applied-configuration': None,
        },
        'clusterName': None,
        'creationTimestamp': None,
        "deletionGracePeriodSeconds": None,
        "deletionTimestamp": None,
        "generateName": None,
        "generation": None,
        "ownerReferences": None,
        "resourceVersion": None,
        "selfLink": None,
        "uid": None,
    },
    "spec": {
        "awsElasticBlockStore": None,
        "azureDisk": None,
        "azureFile": None,
        "cephfs": None,
        "cinder": None,
        "claimRef": {
            "resourceVersion": None,
            "uid": None,
        },
        "fc": None,
        "flexVolume": None,
        "flocker": None,
        "gcePersistentDisk": None,
        "glusterfs": None,
        "hostPath": None,
        "iscsi": None,
        "local": None,
        "mountOptions": None,
        "nfs": None,
        "nodeAffinity": None,
        "photonPersistentDisk": None,
        "portworxVolume": None,
        "quobyte": None,
        "rbd": None,
        "scaleIo": None,
        "storageos": None,
        "vsphereVolume": None,
    },
}


def pv_fname(name: PvName, storage_path: FilePath) -> FilePath:
    return os.path.join(storage_path, name + '.yaml')


def check_sentinel() -> bool:
    logger.info('Check sentinel')
    cms = kclient.list_namespaced_config_map(k_namespace)
    return any(cm.metadata.name == k_sentinel_name for cm in cms.items)


def set_sentinel() -> None:
    logger.info('Set sentinel')
    kclient.create_namespaced_config_map(k_namespace, kubernetes.client.models.V1ConfigMap(
        metadata=kubernetes.client.models.V1ObjectMeta(
            name=k_sentinel_name,
            namespace=k_namespace,
        ),
        data={'sentinel': 'true'},
    ))


def list_remote(storage_class: str) -> List[PvName]:
    logger.info(f'Fetch remote PV with storage class {storage_class}')
    raw = kclient.list_persistent_volume()
    fltr = [k for k in raw.items if k.spec.storage_class_name == storage_class]
    return [k.metadata.name for k in fltr]


def del_recur(obj: dict, fltr: dict):
    sk = [*obj.items()]
    for k, v in sk:
        if k in fltr:
            if fltr[k] is None:
                obj.pop(k)
            else:
                del_recur(v, fltr[k])


def read_remote(name: PvName) -> ReducedPvYaml:
    logger.info(f'Fetch remote PV {name}')
    pv = kclient.read_persistent_volume(name)
    data = kclient.api_client.sanitize_for_serialization(pv)
    del_recur(data, _pv_strip_fields)
    return data


def list_local(storage_path) -> List[PvName]:
    fs = os.listdir(storage_path)
    yaml_fs = [f for f in fs if f.endswith('.yaml')]
    return [f[:-len('.yaml')] for f in yaml_fs]


def read_local(name: PvName, storage_path: FilePath) -> ReducedPvYaml:
    fname = pv_fname(name, storage_path)
    with open(fname, 'r') as in_f:
        data = yaml.safe_load(in_f)
    return data


def save_local(name: PvName, data: ReducedPvYaml, storage_path: str) -> None:
    fname = pv_fname(name, storage_path)
    with open(fname, 'w') as out_f:
        yaml.dump(data, out_f)


def pull_remote(name: PvName, storage_path: FilePath) -> None:
    logger.info(f'Save new PV {name} to {storage_path}')
    data = read_remote(name)
    save_local(name, data, storage_path)


def rm_local(name: PvName, storage_path: str) -> None:
    logger.info(f'Remove deleted PV {name} from {storage_path}')
    fname = pv_fname(name, storage_path)
    os.remove(fname)


def merge_pv(name: PvName, storage_path: FilePath) -> None:
    logger.info(f'Replace updated PV {name} at {storage_path}')
    data_remote = read_remote(name)
    _data_local = read_local(name, storage_path)
    data_merged = data_remote  # just accept remote
    save_local(name, data_merged, storage_path)


def push_pv(name: PvName, storage_path: FilePath) -> None:
    logger.info(f'Restore PV {name}')
    data = read_local(name, storage_path)
    pv = kclient.api_client._ApiClient__deserialize(data, 'V1PersistentVolume')
    kclient.create_persistent_volume(pv)


def sync_all_down(storage_class: str, storage_path: FilePath):
    logger.info(f'Maintenance cycle: pull and save all remote PV under storage class {storage_class}')
    pv_remote = set(list_remote(storage_class))
    pv_local = set(list_local(storage_path))

    pv_all = set.union(pv_remote, pv_local)
    for pv in pv_all:
        if pv in pv_remote and pv not in pv_local:
            pull_remote(pv, storage_path)
        elif pv not in pv_remote and pv in pv_local:
            rm_local(pv, storage_path)
        else:
            merge_pv(pv, storage_path)


def sync_all_up(storage_path: FilePath):
    logger.info(f'Restoration cycle: restore all PV from {storage_path}')
    pv_local = list_local(storage_path)
    for pv in pv_local:
        push_pv(pv, storage_path)


def loop(storage_class: str, storage_path: FilePath):
    logger.info('Wake')
    if check_sentinel():
        sync_all_down(storage_class, storage_path)
    else:
        sync_all_up(storage_path)
        set_sentinel()


def main(interval: int, storage_path: FilePath, storage_class: str):
    logger.info(f'Init PV Saver: interval={interval}, storage_path={storage_path}, storage_class={storage_class}')
    while True:
        loop(storage_class, storage_path)
        time.sleep(interval)


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int)
    parser.add_argument('--storage-path')
    parser.add_argument('--storage-class')
    args = parser.parse_args()
    main(args.interval, args.storage_path, args.storage_class)


if __name__ == '__main__':
    cli()
