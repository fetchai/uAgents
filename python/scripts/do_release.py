"""Release automation script."""

import subprocess
import sys
from pathlib import Path
from typing import Literal

import tomli
from packaging.version import Version
from pydantic_settings import BaseSettings

ROOT = Path(__file__).parent.parent


class Settings(BaseSettings):
    """Settings for release script."""

    # PYPI username
    pypi_username: str

    # PYPI password
    pypi_password: str

    # which package we are releasing
    package: Literal["main", "core"] = "main"


def get_tag_prefix(package: str) -> str:
    """Map package to tag."""

    return {"main": "v", "core": "core@"}[package]


def get_package_path(package: str) -> Path:
    """Get package path."""

    return {"main": ROOT, "core": ROOT / "uagents-core"}[package]



def get_the_latest_release_version(package: str) -> Version:
    """Get release version from gihtub tags."""
    text = subprocess.check_output("git ls-remote --tags origin", shell=True, text=True)
    tags = [i.split("\t")[1].strip() for i in text.splitlines()]
    tag_prefix = "refs/tags/" + get_tag_prefix(package)
    tags = [i for i in tags if i.startswith(tag_prefix) and not i.endswith("^{}")]
    versions = [i.replace(tag_prefix, "") for i in tags]
    return Version(versions[-1]) if len(versions) > 0 else Version("0.0.0")


def get_current_version(package: str) -> Version:
    """Get current code version."""
    text = (get_package_path(package) / "pyproject.toml").read_text()
    version = tomli.loads(text)["tool"]["poetry"]["version"]
    return Version(version)


def do_we_need_to_release(package: str) -> bool:
    """Check is code version is newer than on github."""
    current_version = get_current_version(package)
    released_version = get_the_latest_release_version(package)
    return current_version > released_version


def make_tag(current_version: Version, package: str) -> None:
    """Make git tag."""
    tag_prefix = get_tag_prefix(package)
    tag_text = {
        "main": f"Release {current_version}",
        "core": f"UAgents-Core release {current_version}",
    }[package]
    subprocess.check_call(
        f"git tag {tag_prefix}{current_version} -m '{tag_text}'", shell=True
    )


def push_tag(tag: str) -> None:
    """Push tag to github."""
    subprocess.check_call(f"git push origin {tag}", shell=True)


def make_release(current_version: Version, package: str) -> None:
    """Make release on Github."""
    tag_prefix = get_tag_prefix(package)
    subprocess.check_call(
        f'gh release create {tag_prefix}{current_version} --title "{tag_prefix}{current_version}"'
        " --generate-notes --latest",
        shell=True,
    )


def build_packages(package: str):
    """Build packages."""
    subprocess.check_call("poetry build", cwd=str(get_package_path(package)) , shell=True)


class ReleaseTool:
    """Release helper tool."""

    def __init__(self, settings: Settings) -> None:
        """Init release tool instance."""
        self._settings = settings

    def upload_packages(self):
        """Upload packages to PYPI."""
        result = subprocess.run(
            f"poetry publish --skip-existing --username {self._settings.pypi_username} "
            f"--password {self._settings.pypi_password} --verbose",
            check=True,
            shell=True,
            cwd=str(get_package_path(self._settings.package)),
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        if result.returncode != 0:
            raise RuntimeError("Upload packages failed!")

    def main(self):
        """Run release process."""
        current_version = get_current_version(self._settings.package)
        latest_release_version = get_the_latest_release_version(self._settings.package)

        print("Current version:", current_version)
        print("Latest release version:", latest_release_version)

        if current_version > latest_release_version:
            print("Current version is newer. Good to go.")
        else:
            print("Current version is not newer. Exiting.")
            return

        # copy README.md from top level to python folder so that appears on pypi
        if self._settings.package == "main":
            readme = ROOT.parent / "README.md"
            python_readme = ROOT / "README.md"
            python_readme.write_text(readme.read_text())

        print("\nBuilding packages")
        build_packages(package=self._settings.package)
        print("Packages built")

        print("\nUpload packages")
        self.upload_packages()
        print("Packages uploaded")

        print("\nMake tag")
        make_tag(current_version, package=self._settings.package)
        print("Tag made")

        tag = get_tag_prefix(self._settings.package) + str(current_version)
        print(f"\nPush tag: {tag}")
        push_tag(tag)
        print("Tag pushed")

        print("\nMake release")
        make_release(current_version, package=self._settings.package)
        print("Release made.")

        print("\nDONE")


if __name__ == "__main__":
    settings = Settings() # type: ignore
    ReleaseTool(settings).main()
