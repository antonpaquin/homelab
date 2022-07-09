import argparse

import hashbak.entrypoints
import hashbak.log
import hashbak.remote


def cli_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")

    backup = subparsers.add_parser('backup')
    backup.add_argument('--src-dir')
    backup.add_argument('--salt-hex')
    backup.add_argument('--key-hex')
    backup.add_argument('--s3-bucket')

    restore = subparsers.add_parser('restore')
    restore.add_argument('--snapshot')
    restore.add_argument('--dest-dir')
    restore.add_argument('--salt-hex')
    restore.add_argument('--key-hex')
    restore.add_argument('--s3-bucket')

    return parser.parse_args()


def main():
    hashbak.log.setup_logs()
    args = cli_args()

    if args.cmd == "backup":
        hashbak.entrypoints.backup(
            root=args.src_dir,
            hash_salt=bytes.fromhex(args.salt_hex),
            storage=hashbak.remote.EncryptedS3Storage(
                aes_key=bytes.fromhex(args.key_hex),
                bucket=args.s3_bucket,
            )
        )

    elif args.cmd == "restore":
        hashbak.entrypoints.full_restore(
            name=args.snapshot,
            root=args.dest_dir,
            hash_salt=bytes.fromhex(args.salt_hex),
            storage=hashbak.remote.EncryptedS3Storage(
                aes_key=bytes.fromhex(args.key_hex),
                bucket=args.s3_bucket,
            )
        )
