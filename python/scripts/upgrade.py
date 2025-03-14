"""
A script that walks through all .py files in the respective subdirectory and
executes the shell command "pyupgrade" on each of them to upgrade the code to
the specified Python version.
"""

import argparse
import os
import subprocess
import sys


def upgrade_py_files(folder: str = "./src", tag: str = "--py312-plus"):
    print("Upgrading all .py files in the worker subdirectory...")
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                print(f"Checking {path}...")
                subprocess.run(["pyupgrade", path, tag], check=False)


def parse_version(version: str) -> str:
    if version == "313":
        return "--py313-plus"
    if version == "312":
        return "--py312-plus"
    if version == "311":
        return "--py311-plus"
    if version == "310":
        return "--py310-plus"
    raise ValueError(f"Unknown version tag: {version}")


parser = argparse.ArgumentParser(
    description="Upgrade all .py files in the worker subdirectory."
)
parser.add_argument(
    "--folder",
    type=str,
    default="./src",
    help="The folder in which to upgrade all .py files.",
)
parser.add_argument(
    "--version",
    type=str,
    default="310",
    help="The tag to use for the upgrade.",
)
args: argparse.Namespace = parser.parse_args()

if __name__ == "__main__":
    print(
        f"Upgrading all .py files in the {args.folder} subdirectory to "
        f"Python{args.version[:1]}.{args.version[1:]} ..."
    )
    try:
        input("Press Enter to continue...")
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)
    upgrade_py_files(args.folder, parse_version(args.version))
    print("Done!")
