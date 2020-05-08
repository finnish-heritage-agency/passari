from pathlib import Path

import pytest
from passari.scripts.download_object import cli as download_object_cli


@pytest.fixture(scope="function")
def museum_packages_dir(tmpdir):
    path = Path(tmpdir) / "museum_packages"
    path.mkdir(exist_ok=True)

    return path


@pytest.fixture(scope="function")
def download_object(mock_museumplus, cli):
    def func(args, **kwargs):
        return cli(download_object_cli, args, **kwargs)

    return func


class TestDownloadObject:
    def test_success(self, download_object, museum_packages_dir):
        """
        Download an object with attachments
        """
        result = download_object([
            "--package-dir", str(museum_packages_dir), "1234567"
        ])

        assert result.exit_code == 0

        package_dir = museum_packages_dir / "1234567"
        assert package_dir.is_dir()

        assert package_dir.joinpath("sip", "attachments").is_dir()
        assert package_dir.joinpath("sip", "reports").is_dir()

    def test_success_no_attachments(self, download_object, museum_packages_dir):
        """
        Download an object without attachments
        """
        result = download_object([
            "--package-dir", str(museum_packages_dir), "1234568"
        ])

        assert result.exit_code == 0

        package_dir = museum_packages_dir / "1234568"
        assert package_dir.is_dir()

        assert not package_dir.joinpath("sip", "attachments").is_dir()
        assert package_dir.joinpath("sip", "reports").is_dir()

    def test_success_empty_attachment(
            self, download_object, museum_packages_dir):
        """
        Download an object with an empty attachment
        """
        result = download_object([
            "--package-dir", str(museum_packages_dir), "1234573"
        ])

        assert result.exit_code == 0

        package_dir = museum_packages_dir / "1234573"
        assert package_dir.is_dir()

        assert package_dir.joinpath("sip", "attachments").is_dir()

        # Only "Multimedia.xml" is added
        files = package_dir / "sip" / "attachments" / "1234573001"
        assert len(list(files.iterdir())) == 1
        assert next(files.iterdir()).name == "Multimedia.xml"

    def test_missing_object_id(self, download_object, museum_packages_dir):
        result = download_object([
            "--package-dir", str(museum_packages_dir)
        ], success=False)

        assert "Missing argument 'OBJECT_ID'" in result.stdout
