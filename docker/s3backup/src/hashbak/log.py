import logging
import sys


def setup_logs():
    handler = logging.StreamHandler(sys.stdout)
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(fmt)

    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.DEBUG)

    for name in {'botocore', 'urllib3', 's3transfer'}:
        sublogger = logging.getLogger(name)
        sublogger.setLevel(logging.WARN)
