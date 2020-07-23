from subprocess import CalledProcessError

import pytest
from passari.exceptions import PreservationError

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

IMPORT_OBJECT_JPEG_VERSION_NOT_SUPPORTED_STDERR = """
File "utils.py", line 132, in scrape_file
    raise ValueError(six.ensure_str(error_str))
ValueError: 






File format version is not supported.
"""


@pytest.mark.asyncio
async def test_generate_sip_unsupported_file_format(
        package_dir, museum_package_factory):
    """
    Test generating a SIP with an unsupported file format and ensure
    PreservationError is raised
    """
    museum_package = await museum_package_factory("1234570")

    with pytest.raises(PreservationError) as exc:
        await museum_package.generate_sip()

    assert "Unsupported file format: wad" == exc.value.error


@pytest.mark.asyncio
async def test_generate_sip_invalid_tiff_jhove(
        package_dir, museum_package_factory):
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
        package_dir, museum_package_factory):
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
        package_dir, museum_package_factory, monkeypatch):
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


@pytest.mark.asyncio
async def test_generate_sip_jpeg_mpo_not_supported(
        package_dir, museum_package_factory):
    """
    Test generating a SIP containing a MPO/JPEG file that
    is not supported
    """
    museum_package = await museum_package_factory("1234581")

    with pytest.raises(PreservationError) as exc:
        await museum_package.generate_sip()

    assert "MPO JPEG files not supported" == exc.value.error


@pytest.mark.asyncio
async def test_generate_sip_with_non_ascii_filename(
        package_dir, mock_museumplus, museum_package_factory):
    """
    Test generating a SIP containing an attachment with a non-ASCII filename,
    which are not processed by the DPRES service yet
    """
    with pytest.raises(PreservationError) as exc:
        await museum_package_factory("1234582")

    assert "Filename contains non-ASCII characters" == exc.value.error


@pytest.mark.asyncio
async def test_generate_sip_jpeg_version_not_supported(
        package_dir, museum_package_factory, monkeypatch):
    """
    Test generating a SIP containing a JPEG file with a file format
    that is not supported
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
                    IMPORT_OBJECT_JPEG_VERSION_NOT_SUPPORTED_STDERR.encode(
                        "utf-8"
                    )
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

    assert "JPEG version not supported" == exc.value.error
