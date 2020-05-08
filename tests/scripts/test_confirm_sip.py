import gzip
import json
from pathlib import Path

import lxml.etree

import pytest
from passari.config import CONFIG
from passari.museumplus.settings import ZETCOM_NS
from passari.scripts.confirm_sip import cli as confirm_sip_cli


@pytest.fixture(scope="function")
def museum_packages_dir(tmpdir, museum_package):
    """
    Museum package directory that already has a complete package with
    some log files inside it
    """
    path = Path(tmpdir) / "museum_packages"
    path.mkdir(exist_ok=True)

    museum_package.path.rename(path / "1234567")

    (path / "1234567" / "logs" / "ingest-report.html").write_text(
        "<html><body><p>Success</p></body></html>"
    )
    (path / "1234567" / "logs" / "create-sip.log").write_text(
        "SIP was created"
    )

    return path


@pytest.fixture(scope="function")
def archive_dir(tmpdir):
    path = Path(tmpdir) / "museum_archive"
    path.mkdir(exist_ok=True)

    return path


@pytest.fixture(scope="function")
def confirm_sip(cli, monkeypatch):
    monkeypatch.setitem(
        CONFIG["museumplus"], "object_preservation_field_type",
        "dataField"
    )
    monkeypatch.setitem(
        CONFIG["museumplus"], "object_preservation_field_name",
        "fakePreservationTxt"
    )

    def func(args, **kwargs):
        return cli(confirm_sip_cli, args, **kwargs)

    return func


class TestConfirmSIP:
    def test_success(
            self, confirm_sip, museum_packages_dir, archive_dir,
            mock_museumplus):
        confirm_sip([
            "--package-dir", str(museum_packages_dir),
            "--archive-dir", str(archive_dir),
            "--status", "accepted", "1234567"
        ])

        # The original museum object directory does not exist
        assert not (museum_packages_dir / "1234567").is_dir()

        archive_log_dir = (
            archive_dir / "123" / "456" / "7" / "Object_1234567"
            / "20190102_Object_1234567.tar" / "logs"
        )

        # Archive directory was created and it contains the compressed
        # log files
        assert archive_log_dir.is_dir()
        assert (archive_log_dir / "ingest-report.html.gz").is_file()
        assert (archive_log_dir / "create-sip.log.gz").is_file()

        assert gzip.decompress(
            (archive_log_dir / "create-sip.log.gz").read_bytes()
        ) == b"SIP was created"

        # MuseumPlus was updated with a preservation event
        last_request = mock_museumplus.requests[-1]

        assert last_request["method"] == "PUT"
        assert last_request["url"] == \
            "/module/Object/1234567/fakePreservationTxt"

        xml = lxml.etree.fromstring(last_request["content"])
        module_item = xml.find(
            f"{{{ZETCOM_NS}}}modules//"
            f"{{{ZETCOM_NS}}}moduleItem[@id='1234567']"
        )

        events = json.loads(
            module_item.find(
                f"{{{ZETCOM_NS}}}dataField[@name='fakePreservationTxt']"
                f"{{{ZETCOM_NS}}}value"
            ).text
        )

        assert len(events) == 1
        assert events[0]["filename"] == "20190102_Object_1234567.tar"
        assert events[0]["status"] == "accepted"
        assert events[0]["object_modify_date"] == \
            "2019-01-02T02:10:57.171000+00:00"

    def test_sip_id(
            self, confirm_sip, museum_packages_dir, archive_dir,
            mock_museumplus):
        confirm_sip([
            "--sip-id", "testID",
            "--package-dir", str(museum_packages_dir),
            "--archive-dir", str(archive_dir),
            "--status", "accepted", "1234567"
        ])

        # The original museum object directory does not exist
        assert not (museum_packages_dir / "1234567").is_dir()

        archive_log_dir = (
            archive_dir / "123" / "456" / "7" / "Object_1234567"
            / "20190102_Object_1234567-testID.tar" / "logs"
        )

        # Archive directory was created and it contains the compressed
        # log files
        assert archive_log_dir.is_dir()
        assert (archive_log_dir / "ingest-report.html.gz").is_file()
        assert (archive_log_dir / "create-sip.log.gz").is_file()

        assert gzip.decompress(
            (archive_log_dir / "create-sip.log.gz").read_bytes()
        ) == b"SIP was created"

        # MuseumPlus was updated with a preservation event
        last_request = mock_museumplus.requests[-1]

        assert last_request["method"] == "PUT"
        assert last_request["url"] == \
            "/module/Object/1234567/fakePreservationTxt"

        xml = lxml.etree.fromstring(last_request["content"])
        module_item = xml.find(
            f"{{{ZETCOM_NS}}}modules//"
            f"{{{ZETCOM_NS}}}moduleItem[@id='1234567']"
        )

        events = json.loads(
            module_item.find(
                f"{{{ZETCOM_NS}}}dataField[@name='fakePreservationTxt']"
                f"{{{ZETCOM_NS}}}value"
            ).text
        )

        assert len(events) == 1
        assert events[0]["filename"] == "20190102_Object_1234567-testID.tar"
        assert events[0]["status"] == "accepted"
        assert events[0]["object_modify_date"] == \
            "2019-01-02T02:10:57.171000+00:00"

    def test_disable_log_entry(
            self, confirm_sip, museum_packages_dir, archive_dir,
            mock_museumplus, monkeypatch):
        """
        Run 'confirm-sip' without adding a log entry to the MuseumPlus
        entry
        """
        monkeypatch.setitem(
            CONFIG["museumplus"], "add_log_entries", False
        )

        confirm_sip([
            "--package-dir", str(museum_packages_dir),
            "--archive-dir", str(archive_dir),
            "--status", "accepted", "1234567"
        ])

        # MuseumPlus was not updated
        assert not any(
            request["method"] == "PUT" for request in mock_museumplus.requests
        )
