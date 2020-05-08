import datetime
import pytest

from passari.museumplus.db import get_museum_object


class TestMuseumObject:
    def test_sip_name(self, museum_object):
        assert museum_object.sip_name == "20190102_Object_1234567"

    def test_object_id(self, museum_object):
        assert museum_object.object_id == "1234567"

    def test_created_date(self, museum_object):
        assert museum_object.created_date == datetime.datetime(
            1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc
        )

    def test_modified_date(self, museum_object):
        assert museum_object.modified_date == datetime.datetime(
            2019, 1, 2, 2, 10, 57, 171000, tzinfo=datetime.timezone.utc
        )

    def test_title(self, museum_object):
        assert museum_object.title == "Jonkinlainen testiaineisto"

    def test_attachment_ids(self, museum_object):
        assert museum_object.attachment_ids == [
            1234567001, 1234567002
        ]

    def test_collection_activity_ids(self, load_museum_object):
        museum_object = load_museum_object("1234579")
        assert museum_object.collection_activity_ids == [
            765432001, 765432002
        ]


class TestMuseumAttachment:
    def test_filename(self, museum_attachment):
        assert museum_attachment.filename == "kuva1.JPG"

    def test_filename_not_found(self, load_museum_attachment):
        # If the filename isn't found in the XML document, use a
        # generated name
        museum_attachment = load_museum_attachment("1234573001")

        assert museum_attachment.filename == "Multimedia_1234573001.attachment"

    def test_attachment_id(self, museum_attachment):
        assert museum_attachment.attachment_id == "1234567001"


class TestMuseumObjectDownload:
    @pytest.mark.asyncio
    async def test_get_museum_object(self, museum_session, mock_museumplus):
        """
        Use a mocked MuseumPlus server to download an Object
        """
        museum_object = await get_museum_object(
            session=museum_session,
            object_id=1234567)

        assert museum_object.object_id == "1234567"

    @pytest.mark.asyncio
    async def test_get_museum_object_truncated(
            self, museum_session, mock_museumplus):
        """
        Try downloading a barebones Object document and check it causes an
        exception
        """
        with pytest.raises(IOError) as exc:
            await get_museum_object(
                session=museum_session,
                object_id=1234578
            )

        assert "Received a truncated XML document" in str(exc.value)
