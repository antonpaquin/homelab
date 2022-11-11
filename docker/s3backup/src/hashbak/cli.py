import argparse

import hashbak.entrypoints
import hashbak.log
import hashbak.remote


def cli_args():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="cmd")

    backup = subparsers.add_parser('backup')
    backup.add_argument('--src-dir', required=True)
    backup.add_argument('--salt-hex', required=True)
    backup.add_argument('--key-hex', required=True)
    backup.add_argument('--s3-bucket', required=True)

    restore = subparsers.add_parser('restore')
    restore.add_argument('--snapshot', required=True)
    restore.add_argument('--dest-dir', required=True)
    restore.add_argument('--salt-hex', required=True)
    restore.add_argument('--key-hex', required=True)
    restore.add_argument('--s3-bucket', required=True)

    list_ = subparsers.add_parser('list')
    list_.add_argument('--s3-bucket', required=True)

    show = subparsers.add_parser('show')
    show.add_argument('--snapshot', required=True)
    show.add_argument('--s3-bucket', required=True)
    show.add_argument('--key-hex', required=True)

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

    elif args.cmd == "list":
        hashbak.entrypoints.list_snapshots(
            storage=hashbak.remote.EncryptedS3Storage(
                aes_key=b'',
                bucket=args.s3_bucket,
            )
        )

    elif args.cmd == "show":
        hashbak.entrypoints.show_snapshot(
            name=args.snapshot,
            storage=hashbak.remote.EncryptedS3Storage(
                aes_key=bytes.fromhex(args.key_hex),
                bucket=args.s3_bucket,
            )
        )

if __name__ == '__main__':
    main()
