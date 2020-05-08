from subprocess import CalledProcessError

import lxml.etree

import pytest
from passari.dpres.package import MuseumObjectPackage
from passari.exceptions import PreservationError
from tests.util import is_image_file, is_xml_file

METS_NS = "http://www.loc.gov/METS/"
PREMIS_NS = "info:lc/xmlns/premis-v2"


class TestMuseumPackageDownload:
    @pytest.mark.asyncio
    async def test_download_package(
            self, load_museum_object, package_dir, mock_museumplus):
        """
        Download the package and ensure all the files are in place
        """
        museum_object = load_museum_object(object_id="1234567")
        museum_package = await museum_object.download_package(package_dir)

        assert is_xml_file(museum_package.report_dir.joinpath("lido.xml"))
        assert is_xml_file(museum_package.report_dir.joinpath("Object.xml"))

        assert is_image_file(
            museum_package.attachment_dir / "1234567001" / "kuva1.JPG"
        )
        assert is_xml_file(
            museum_package.attachment_dir / "1234567001" / "Multimedia.xml"
        )

        assert is_image_file(
            museum_package.attachment_dir / "1234567002" / "kuva2.JPG"
        )
        assert is_xml_file(
            museum_package.attachment_dir / "1234567002" / "Multimedia.xml"
        )

    @pytest.mark.asyncio
    async def test_download_package_leftover_attachments(
            self, load_museum_object, package_dir, mock_museumplus):
        """
        Download the package to an existing directory containing attachments
        that don't belong to the museum object anymore
        """
        (package_dir / "sip" / "attachments" / "100200").mkdir(parents=True)
        (package_dir / "sip" / "attachments" / "100200" / "fake.jpg").touch()
        (package_dir / "sip" / "attachments" / "100300").mkdir(parents=True)
        (package_dir / "sip" / "attachments" / "100300" / "fake.jpg").touch()

        museum_object = load_museum_object(object_id="1234567")
        await museum_object.download_package(package_dir)

        # The old directories were removed when downloading the attachments
        assert not (package_dir / "sip" / "attachments" / "100200").is_dir()
        assert not (package_dir / "sip" / "attachments" / "100300").is_dir()
        assert (package_dir / "sip" / "attachments" / "1234567001").is_dir()
        assert (package_dir / "sip" / "attachments" / "1234567002").is_dir()

    @pytest.mark.asyncio
    async def test_download_package_leftover_collection_activities(
            self, load_museum_object, package_dir, mock_museumplus):
        """
        Download the package to an existing directory containing
        collection activites that don't belong to the museum object anymore
        """
        collection_activity_dir = package_dir / "sip" / "collection_activities"
        (collection_activity_dir / "765432001").mkdir(parents=True)
        (collection_activity_dir / "10101010").mkdir(parents=True)
        (collection_activity_dir / "10101010" / "test.xml").touch()

        museum_object = load_museum_object(object_id="1234579")
        await museum_object.download_package(package_dir)

        # The old directory (10101010) was removed
        assert not (collection_activity_dir / "10101010").is_dir()
        assert (collection_activity_dir / "765432001").is_dir()

    @pytest.mark.asyncio
    async def test_downloads_cached(
            self, museum_object, mock_museumplus, package_dir):
        REQUEST_URLS = [
            "/module/Multimedia/1234567001", "/module/Multimedia/1234567002",
            "/module/Multimedia/1234567001/attachment",
            "/module/Object/1234567/export/45005"
        ]

        await museum_object.download_package(package_dir)

        # Every request should have been made once
        for url in REQUEST_URLS:
            assert mock_museumplus.request_counters[url] == 1

        await museum_object.download_package(package_dir)

        # Files already exist in the file system and no requests are made
        for url in REQUEST_URLS:
            assert mock_museumplus.request_counters[url] == 1


class TestMuseumObjectPackageSIP:
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_sip(self, museum_package, extract_tar):
        """
        Test generating a SIP from a downloaded museum package
        """
        await museum_package.generate_sip()

        # Test that the SIP was created
        assert museum_package.sip_archive_path.is_file()

        # Test that logs exist
        for name in ("compile-mets", "compile-structmap", "compress",
                     "create-mix", "import-object", "premis-event",
                     "sign-mets"):
            assert (museum_package.log_dir / f"{name}.log").is_file()

        # Workspace should be empty
        assert museum_package.workspace_dir.is_dir()
        assert not list(museum_package.workspace_dir.glob("*"))

        # No collection activities linked to this Object
        assert not museum_package.collection_activity_dir.is_dir()

        # Extract TAR and ensure files inside it exist
        tar_path = extract_tar(museum_package.sip_archive_path)

        assert (tar_path / "signature.sig").is_file()
        assert (tar_path / "mets.xml").is_file()
        assert (tar_path / "reports" / "lido.xml").is_file()
        assert (
            tar_path / "attachments" / "1234567001" / "kuva1.JPG"
        ).is_file()
        assert (
            tar_path / "attachments" / "1234567002" / "kuva2.JPG"
        ).is_file()

        xml = lxml.etree.parse(str(tar_path / "mets.xml"))

        # Check that mets.xml contains expected entries
        # lido.xml was embedded
        assert len(
            xml.findall(
                f"{{{METS_NS}}}dmdSec//"
                f"{{{METS_NS}}}mdWrap[@MDTYPE='LIDO']"
            )
        ) == 1

        # Contains 'creation' event
        event = xml.find(
            f"{{{METS_NS}}}amdSec//"
            f"{{{METS_NS}}}digiprovMD//"
            f"{{{METS_NS}}}mdWrap[@MDTYPE='PREMIS:EVENT']//"
            f"{{{PREMIS_NS}}}event/"
            f"{{{PREMIS_NS}}}eventDetail[.='Object database entry creation']/.."
        )
        assert event.find(f"{{{PREMIS_NS}}}eventType").text == "creation"
        assert event.find(f"{{{PREMIS_NS}}}eventDateTime").text == \
            "1970-01-01T00:00:00+00:00"
        assert event.find(f"{{{PREMIS_NS}}}eventDetail").text == \
            "Object database entry creation"

        # Files were imported with correct IDs
        file_ids = [
            "Multimedia:1234567001:Multimedia.xml",
            "Multimedia:1234567001:kuva1.JPG",
            "Multimedia:1234567002:Multimedia.xml",
            "Multimedia:1234567002:kuva2.JPG",
            "Object:1234567:reports/Object.xml",
            "Object:1234567:reports/lido.xml",
        ]
        for file_id in file_ids:
            assert len(xml.findall(
                f"{{{METS_NS}}}amdSec//{{{METS_NS}}}techMD//"
                f"{{{PREMIS_NS}}}objectIdentifierValue[.='{file_id}']"
            )) == 1

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_sip_with_archive(
            self, museum_package_factory, extract_tar):
        """
        Test generating a SIP from a downloaded museum package that
        has a ZIP file
        """
        museum_package = await museum_package_factory("1234569")
        await museum_package.generate_sip()

        # SIP was generated
        assert museum_package.sip_archive_path.is_file()

        # 'extract-archive.log' exists
        assert (museum_package.log_dir / "extract-archive.log").is_file()

        tar_path = extract_tar(museum_package.sip_archive_path)

        # Ensure the TAR was extracted corrctly
        assert (
            tar_path / "attachments" / "1234569001" / "test.zip" / "kuva1.JPG"
        ).is_file()
        assert (
            tar_path / "attachments" / "1234569001" / "test.zip" / "kuva2.JPG"
        ).is_file()

        xml = lxml.etree.parse(str(tar_path / "mets.xml"))

        # Files were imported with correct IDs
        file_ids = [
            "Multimedia:1234569001:Multimedia.xml",
            "Multimedia:1234569001:test.zip/kuva1.JPG",
            "Multimedia:1234569001:test.zip/kuva2.JPG",
            "Object:1234569:reports/Object.xml",
            "Object:1234569:reports/lido.xml",
        ]
        for file_id in file_ids:
            assert len(xml.findall(
                f"{{{METS_NS}}}amdSec//{{{METS_NS}}}techMD//"
                f"{{{PREMIS_NS}}}objectIdentifierValue[.='{file_id}']"
            )) == 1

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_sip_with_collection_activities(
            self, package_dir, museum_package_factory, extract_tar):
        """
        Generate a SIP from an Object with two related CollectioActivity
        entries
        """
        museum_package = await museum_package_factory("1234579")
        await museum_package.generate_sip()

        # SIP was generated
        assert museum_package.sip_archive_path.is_file()

        tar_path = extract_tar(museum_package.sip_archive_path)

        # Ensure the TAR was extracted corrctly
        assert (
            tar_path / "collection_activities" / "765432001"
            / "CollectionActivity.xml"
        ).is_file()
        assert (
            tar_path / "collection_activities" / "765432002"
            / "CollectionActivity.xml"
        ).is_file()

        xml = lxml.etree.parse(str(tar_path / "mets.xml"))

        # Files were imported with correct IDs
        file_ids = [
            "Object:1234579:reports/Object.xml",
            "Object:1234579:reports/lido.xml",
            "CollectionActivity:765432001:CollectionActivity.xml",
            "CollectionActivity:765432002:CollectionActivity.xml",
        ]
        for file_id in file_ids:
            assert len(xml.findall(
                f"{{{METS_NS}}}amdSec//{{{METS_NS}}}techMD//"
                f"{{{PREMIS_NS}}}objectIdentifierValue[.='{file_id}']"
            )) == 1

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_generate_sip_with_sip_id(
            self, package_dir, museum_package_factory):
        """
        Test generating a SIP with an unique filename using the 'sip_id'
        parameter
        """
        museum_package = await museum_package_factory(
            "1234567", sip_id="testID"
        )
        await museum_package.generate_sip()

        assert (package_dir / "20190102_Object_1234567-testID.tar").is_file()


IMPORT_OBJECT_JPEG_UNSUPPORTED_STDERR = """
  File "import_object.py", line 236, in add_premis_md
    charset=charset)
  File "import_object.py", line 197, in _scrape_file
    raise ValueError(error_str)
ValueError: MIME type image/jpeg with version JPEG image data is not supported.
"""


IMPORT_OBJECT_JPEG_MIME_TYPE_ERROR_STDERR = """
  File "import_object.py", line 236, in add_premis_md
    charset=charset)
  File "import_object.py", line 197, in _scrape_file
    raise ValueError(error_str)
ValueError: MIME type not supported by this scraper.
"""


class TestMuseumObjectPackagePreservationError:
    @pytest.mark.asyncio
    async def test_generate_sip_unsupported_file_format(
            self, package_dir, museum_package_factory):
        """
        Test generating a SIP with an unsupported file format and ensure
        PreservationError is raised
        """
        museum_package = await museum_package_factory("1234570")

        with pytest.raises(PreservationError) as exc:
            await museum_package.generate_sip()

        assert "Unsupported file format: wad" == exc.value.error

    @pytest.mark.asyncio
    async def test_generate_sip_jpeg_version_not_detected(
            self, package_dir, museum_package_factory, monkeypatch):
        """
        Test generating a SIP with a JPEG file that can't be detected correctly
        yet and ensure PreservationError is raised
        """
        # Monkeypatch 'import_object' since reproducing the error would
        # otherwise require the exact same versions of file and FIDO as
        # used in production
        async def mock_import_object(path, *args, **kwargs):
            from passari.dpres.scripts import import_object

            if path.name == "test.JPG":
                raise CalledProcessError(
                    cmd=["import-object", str(path)],
                    returncode=1,
                    output=b"",
                    stderr=IMPORT_OBJECT_JPEG_UNSUPPORTED_STDERR.encode("utf-8")
                )
            else:
                return await import_object(path, *args, **kwargs)

        monkeypatch.setattr(
            "passari.dpres.package.import_object",
            mock_import_object
        )

        museum_package = await museum_package_factory("1234576")

        with pytest.raises(PreservationError) as exc:
            await museum_package.generate_sip()

        assert "JPEG version not detected correctly" == exc.value.error

    @pytest.mark.asyncio
    async def test_generate_sip_invalid_tiff_jhove(
            self, package_dir, museum_package_factory):
        """
        Test generating a SIP containing a TIFF file known to be invalid
        by JHOVE, and ensure PreservationError is raised
        """
        museum_package = await museum_package_factory("1234577")

        with pytest.raises(PreservationError) as exc:
            await museum_package.generate_sip()

        assert "TIFF file failed JHOVE validation" == exc.value.error

    @pytest.mark.asyncio
    async def test_generate_sip_multipage_tiff_not_allowed(
            self, package_dir, museum_package_factory):
        """
        Test generating a SIP containing a multi-page TIFF which is not
        allowed in the DPRES service
        """
        museum_package = await museum_package_factory("1234580")

        with pytest.raises(PreservationError) as exc:
            await museum_package.generate_sip()

        assert "Multi-page TIFF not allowed" == exc.value.error

    @pytest.mark.asyncio
    async def test_generate_sip_jpeg_mime_type_not_detected(
            self, package_dir, museum_package_factory, monkeypatch):
        """
        Test generating a SIP containing a JPEG that does not pass
        MIME type detection due to an issue in file-scraper's PilScraper
        """
        # Monkeypatch 'import_object' since reproducing the error would
        # since the image file containing the exact flaw can't be distributed
        # publicly
        async def mock_import_object(path, *args, **kwargs):
            from passari.dpres.scripts import import_object

            if path.name == "test.JPG":
                raise CalledProcessError(
                    cmd=["import-object", str(path)],
                    returncode=1,
                    output=b"",
                    stderr=(
                        IMPORT_OBJECT_JPEG_MIME_TYPE_ERROR_STDERR.encode("utf-8")
                    )
                )
            else:
                return await import_object(path, *args, **kwargs)

        monkeypatch.setattr(
            "passari.dpres.package.import_object",
            mock_import_object
        )

        museum_package = await museum_package_factory("1234576")

        with pytest.raises(PreservationError) as exc:
            await museum_package.generate_sip()

        assert "JPEG MIME type detection failed" == exc.value.error


class TestMuseumObjectPackage:
    def test_all_files(self, museum_package):
        assert len(museum_package.all_files) == 6

        all_files = museum_package.all_files

        for name in ("Object.xml", "lido.xml", "kuva1.JPG", "kuva2.JPG"):
            assert any([x.name.endswith(name) for x in all_files])

        assert len([
            x for x in all_files
            if x.name.endswith("Multimedia.xml")
        ]) == 2

    def test_image_files(self, museum_package):
        assert len(museum_package.image_files) == 2
        for filename in ("kuva1.JPG", "kuva2.JPG"):
            assert any(
                file_ for file_ in museum_package.image_files
                if file_.name.endswith(filename)
            )

    def test_attachments(self, museum_package):
        for filename in ("kuva1.JPG", "kuva2.JPG"):
            assert any(
                attachment for attachment in museum_package.attachments
                if attachment.filename == filename
            )

    def test_sip_filename(self, museum_package):
        assert museum_package.sip_filename == "20190102_Object_1234567.tar"

    @pytest.mark.asyncio
    async def test_load_attachments(self, museum_package):
        """
        Test that already downloaded attachments are detected correctly
        """
        assert len(museum_package.attachments) == 2
        museum_package.attachments = []

        # Attachments will be rechecked when loading from an existing path
        museum_package = MuseumObjectPackage.from_path_sync(
            path=museum_package.path
        )
        assert len(museum_package.attachments) == 2
        assert set([
            attach.filename for attach in museum_package.attachments
        ]) == set(["kuva1.JPG", "kuva2.JPG"])

        # If the Multimedia.xml file doesn't exist, the attachment won't be
        # loaded
        (museum_package.attachment_dir / "1234567001"
         / "Multimedia.xml").unlink()

        museum_package.load_attachments()
        assert len(museum_package.attachments) == 1
