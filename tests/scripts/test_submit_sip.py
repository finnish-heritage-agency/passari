import subprocess
import time
from pathlib import Path

import pytest
from passari.config import CONFIG
from passari.scripts.submit_sip import cli as submit_sip_cli


PRIVATE_KEY_PATH = Path(__file__).parent.resolve() / "data" / "test_id_rsa"


def run_sftp_server(path, port):
    key_file_path = Path(__file__).parent / "data" / "test_rsa.key"
    key_file_path = key_file_path.resolve()

    process = subprocess.Popen([
        "sftpserver", "--port", str(port), "--keyfile", str(key_file_path)
    ], cwd=str(path), stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    return process


@pytest.fixture(scope="function")
def sftp_dir(tmpdir, unused_tcp_port, monkeypatch):
    """
    Returns a SFTP directory that is served by a local test SFTP server
    """
    monkeypatch.setitem(CONFIG["ssh"], "host", "127.0.0.1")
    monkeypatch.setitem(CONFIG["ssh"], "port", str(unused_tcp_port))
    monkeypatch.setitem(CONFIG["ssh"], "private_key", str(PRIVATE_KEY_PATH))

    sftp_dir = Path(tmpdir) / "sftp"
    sftp_dir.mkdir(exist_ok=True)

    sftp_dir.joinpath("transfer").mkdir(exist_ok=True)

    process = run_sftp_server(path=sftp_dir, port=unused_tcp_port)
    time.sleep(0.5)
    yield sftp_dir

    process.terminate()


@pytest.fixture(scope="function")
def submit_sip(cli):
    def func(args, **kwargs):
        return cli(submit_sip_cli, args, **kwargs)

    return func


class TestSubmitSIP:
    def test_success(
            self, submit_sip, sftp_dir, museum_package_dir,
            museum_packages_dir):
        # Copy the test package into place
        museum_package_dir.joinpath(
            "20190102_Object_1234567.tar"
        ).write_text("testPACKAGEhere")

        submit_sip(["--package-dir", str(museum_packages_dir), "1234567"])

        # The test package is copied to the remote host
        assert sftp_dir.joinpath(
            "transfer", "20190102_Object_1234567.tar"
        ).read_text() == "testPACKAGEhere"

    def test_sip_id(
            self, submit_sip, sftp_dir, museum_package_dir,
            museum_packages_dir):
        museum_package_dir.joinpath(
            "20190102_Object_1234567-testID.tar"
        ).write_text("testPACKAGEhere")

        submit_sip([
            "--package-dir", str(museum_packages_dir), "--sip-id", "testID",
            "1234567"
        ])

        # The test package with a SIP ID is copied to the remote host
        assert sftp_dir.joinpath(
            "transfer", "20190102_Object_1234567-testID.tar"
        ).read_text() == "testPACKAGEhere"
