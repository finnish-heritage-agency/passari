from pathlib import Path

import lxml.etree
import pytest
from passari.scripts.create_sip import cli as create_sip_cli

METS_NS = "http://www.loc.gov/METS/"
PREMIS_NS = "info:lc/xmlns/premis-v2"


@pytest.fixture(scope="function")
def museum_package_dir(tmpdir, museum_package):
    """
    Museum package directory that already has one downloaded package
    inside it
    """
    path = Path(tmpdir) / "museum_packages"
    path.mkdir(exist_ok=True)

    museum_package.path.rename(path / "1234567")

    return path


@pytest.fixture(scope="function")
def create_sip(cli):
    def func(args, **kwargs):
        return cli(create_sip_cli, args, **kwargs)

    return func


class TestCreateSIP:
    @pytest.mark.slow
    def test_success(self, create_sip, museum_package_dir, extract_tar):
        """
        Test creating a submission SIP
        """
        create_sip([
            "--package-dir", str(museum_package_dir),
            "--create-date", "2019-12-03T13:30:45+00:00",
            "1234567"
        ])

        package_dir = museum_package_dir / "1234567"
        assert package_dir.is_dir()

        assert (package_dir / "20190102_Object_1234567.tar").is_file()
        assert (package_dir / "workspace").is_dir()

        tar_path = extract_tar(package_dir / "20190102_Object_1234567.tar")
        xml = lxml.etree.parse(str(tar_path / "mets.xml"))

        # METS header contains expected date entries
        mets_hdr = xml.find(f"{{{METS_NS}}}metsHdr")
        assert mets_hdr.attrib["RECORDSTATUS"] == "submission"
        assert mets_hdr.attrib["CREATEDATE"] == "2019-12-03T13:30:45+00:00"

        # Find the agent name for Passari and ensure the version number
        # is included
        agent_name = xml.xpath(
            "mets:amdSec//mets:digiprovMD//"
            "premis:agentName[starts-with(., 'passari-v')]",
            namespaces={"mets": METS_NS, "premis": PREMIS_NS}
        )[0].text
        version = agent_name.replace("passari-v", "").split(".")

        # The version number should be numeric
        assert version[0].isdigit()

    @pytest.mark.slow
    def test_update(self, create_sip, museum_package_dir, extract_tar):
        """
        Test creating an update SIP
        """
        create_sip([
            "--package-dir", str(museum_package_dir), "--update",
            "--create-date", "2019-12-01T12:15:20+00:00",
            "--modify-date", "2019-12-02T12:20:25+00:00",
            "1234567"
        ])

        package_dir = museum_package_dir / "1234567"
        assert package_dir.is_dir()

        tar_path = extract_tar(package_dir / "20190102_Object_1234567.tar")
        xml = lxml.etree.parse(str(tar_path / "mets.xml"))

        # METS header contains expected date entries for an update SIP
        mets_hdr = xml.find(f"{{{METS_NS}}}metsHdr")
        assert mets_hdr.attrib["RECORDSTATUS"] == "update"
        assert mets_hdr.attrib["CREATEDATE"] == "2019-12-01T12:15:20+00:00"
        assert mets_hdr.attrib["LASTMODDATE"] == "2019-12-02T12:20:25+00:00"

    @pytest.mark.slow
    def test_sip_id(self, create_sip, museum_package_dir):
        result = create_sip([
            "--package-dir", str(museum_package_dir),
            "--sip-id", "testID",
            "1234567"
        ])

        assert result.exit_code == 0

        (museum_package_dir / "1234567"
                            / "20190102_Object_1234567-testID.tar").is_file()

    def test_missing_object_id(self, create_sip, museum_package_dir):
        result = create_sip([
            "--package-dir", str(museum_package_dir)
        ], success=False)

        assert "Missing argument 'OBJECT_ID'" in result.stdout

    def test_invalid_date(self, create_sip, museum_package_dir):
        result = create_sip([
            "--package-dir", str(museum_package_dir),
            "--create-date", "2011-01-99",
            "1234567"
        ], success=False)

        assert (
            "Invalid value for '--create-date': invalid ISO 8601 string"
            in result.stdout
        )
