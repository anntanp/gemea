# Author: Etienne Posthumus

import os
import sys
import argparse


def link_nq_files(src_dir: str, dst_dir: str) -> None:
    os.makedirs(dst_dir, exist_ok=True)

    for root, _, files in os.walk(src_dir):
        for filename in files:
            if not filename.endswith(".nq"):
                continue

            src_path = os.path.join(root, filename)
            dst_path = os.path.join(dst_dir, filename)

            if os.path.exists(dst_path):
                print(f"SKIP (exists): {dst_path}")
                continue

            os.link(src_path, dst_path)
            print(f"LINKED: {src_path} -> {dst_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Hard-link all .nq files from a source directory tree into a flat destination directory."
    )
    parser.add_argument("src", help="Source directory to walk")
    parser.add_argument("dst", help="Destination directory for hard links")
    args = parser.parse_args()

    if not os.path.isdir(args.src):
        print(f"Error: source '{args.src}' is not a directory", file=sys.stderr)
        sys.exit(1)

    link_nq_files(args.src, args.dst)


if __name__ == "__main__":
    main()
