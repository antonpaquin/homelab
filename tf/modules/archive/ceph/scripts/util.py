import subprocess
from typing import List


def get_bind_addr():
    ip_raw = subprocess.check_output(["ip", "addr", "show"]).decode('utf-8')
    ip_line = [line for line in ip_raw.split('\n') if 'inet' in line and 'eth0' in line][0]
    ip_cidr = ip_line.split()[1]
    ip_bind = ip_cidr.split('/')[0]
    return ip_bind


def shell(cmd: List[str]):
    try:
        print(' '.join(cmd), flush=True)
        return subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        print(e, flush=True)
        if e.stdout:
            print('stdout: ', e.stdout, flush=True)
        if e.stderr:
            print('stderr: ', e.stderr, flush=True)
        raise
