import random
import shutil
import string
import subprocess
from pathlib import Path

import pytest
from passari.config import CONFIG
from tests.dpres.conftest import *
from tests.museumplus.conftest import *


def pytest_addoption(parser):
    parser.addoption(
        "--slow", action="store_true", default=False, help="run slow tests"
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--slow"):
        return

    skip_slow = pytest.mark.skip(reason="run slow tests with --slow")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(scope="function", autouse=True)
def cache_dir(tmpdir, monkeypatch):
    """
    Fixture to return the test XDG cache directory

    This directory will contain MuseumPlus session-related files
    """
    (tmpdir / ".cache").mkdir()
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmpdir / ".cache"))

    yield Path(tmpdir / ".cache")


@pytest.fixture(scope="function")
def museum_packages_dir(tmpdir, monkeypatch):
    """
    Fixture pointing to a directory containing museum packages
    """
    path = Path(tmpdir) / "MuseumPackages"
    path.mkdir(exist_ok=True)

    return path


@pytest.fixture(scope="function")
def museum_package_dir(museum_packages_dir):
    """
    Fixture pointing to a directory for a single museum package
    """
    package_dir_ = museum_packages_dir / "1234567"

    package_dir_.mkdir()
    package_dir_.joinpath("sip").mkdir()
    package_dir_.joinpath("sip", "reports").mkdir()

    shutil.copyfile(
        Path(__file__).parent.resolve()
        / "museumplus" / "data" / "museumplus_mock" / "module" / "Object"
        / "1234567.xml",
        package_dir_ / "sip" / "reports" / "Object.xml"
    )

    return package_dir_


@pytest.fixture(scope="function")
def extract_tar(tmpdir):
    """
    Extract the given TAR archive to a temporary directory
    and return the path to allow the TAR archive's contents to be inspected
    """
    root_path = Path(tmpdir) / "TARs"
    root_path.mkdir(exist_ok=True)

    def func(path):
        # Create a random directory for the TAR
        dir_name = "".join([
            random.choice(string.ascii_uppercase + string.ascii_lowercase)
            for _ in range(0, 16)
        ])
        tar_path = root_path / dir_name
        tar_path.mkdir()
        subprocess.run(["tar", "-xf", str(path), "-C", str(tar_path)])

        return tar_path

    return func
