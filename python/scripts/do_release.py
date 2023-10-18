"""Release automation script."""

import os
import subprocess
import sys
from pathlib import Path

import tomli
from packaging.version import Version


ROOT = Path(__file__).parent.parent


class EnvCredentials:
    """Credentials from env variables."""

    @property
    def pypi_username(self) -> str:
        """Get PYPI username."""
        return os.environ.get("PYPI_USERNAME") or ""

    @property
    def pypi_password(self) -> str:
        """Get PYPI password."""
        return os.environ.get("PYPI_PASSWORD") or ""


def get_the_latest_release_version() -> Version:
    """Get release version from gihtub tags."""
    text = subprocess.check_output("git ls-remote --tags origin", shell=True, text=True)
    tags = [i.split("\t")[1].strip() for i in text.splitlines()]
    tags = [i for i in tags if i.startswith("refs/tags/v") and not i.endswith("^{}")]
    versions = [i.replace("refs/tags/v", "") for i in tags]
    return Version(versions[-1])


def get_current_version() -> Version:
    """Get current code version."""
    text = (ROOT / "pyproject.toml").read_text()
    version = tomli.loads(text)["tool"]["poetry"]["version"]
    return Version(version)


def do_we_need_to_release() -> bool:
    """Check is code version is newer than on github."""
    current_version = get_current_version()
    released_version = get_the_latest_release_version()
    return current_version > released_version


def make_tag(current_version: Version) -> None:
    """Make git tag."""
    subprocess.check_call(
        f"git tag v{current_version} -m 'Release {current_version}'", shell=True
    )


def push_tag(current_version) -> None:
    """Push tag to github."""
    subprocess.check_call(f"git push origin v{current_version}", shell=True)


def make_release(current_version: Version) -> None:
    """Make release on Github."""
    subprocess.check_call(
        f"""gh release create v{current_version} --title "v{current_version}"
        --generate-notes --latest""",
        shell=True,
    )


def build_packages():
    """Build packages."""
    subprocess.check_call("poetry build", shell=True)


class ReleaseTool:
    """Release helper tool."""

    def __init__(self, credentials: EnvCredentials) -> None:
        """Init release tool instance."""
        self._credentials = credentials

    def upload_packages(self):
        """Upload packages to PYPI."""
        result = subprocess.run(
            f"poetry publish --skip-existing --username {self._credentials.pypi_username} "
            f"--password {self._credentials.pypi_password} --verbose",
            check=True,
            shell=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        if result.returncode != 0:
            raise RuntimeError("Upload pacakges failed!")

    def main(self):
        """Run release process."""
        current_version = get_current_version()
        latest_release_version = get_the_latest_release_version()

        print("Current version:", current_version)
        print("Latest release version:", latest_release_version)

        if current_version > latest_release_version:
            print("Current version is newer. Good to go.")
        else:
            print("Current version is not newer. Exiting.")
            return

        print("\nBuilding packages")
        build_packages()
        print("Packages built")

        print("\nUpload packages")
        self.upload_packages()
        print("Packages uploaded")

        print("\nMake tag")
        make_tag(current_version)
        print("Tag made")

        print("\nPush tag")
        push_tag(current_version)
        print("Tag pushed")

        print("\nMake release")
        make_release(current_version)
        print("Release made." "")

        print("\nDONE")


if __name__ == "__main__":
    creds = EnvCredentials()
    ReleaseTool(creds).main()
