import lxml.etree

import pytest
from aiohttp.client_exceptions import ClientResponseError
from passari.museumplus.fields import (add_preservation_event,
                                              get_object_field,
                                              set_object_field)
from passari.museumplus.settings import ZETCOM_NS


@pytest.mark.asyncio
async def test_get_object_field(museum_session, mock_museumplus):
    """
    Test retrieving a given field from an Object
    """
    # Field exists
    assert await get_object_field(
        session=museum_session, object_id=1234567,
        name="ObjObjectNumberTxt"
    ) == "TEST1337:21"

    # Field does not exist
    assert not await get_object_field(
        session=museum_session, object_id=1234567, name="FakeTxt"
    )


@pytest.mark.asyncio
async def test_set_object_field(museum_session, mock_museumplus):
    """
    Test updating an object field by checking that a correctly formed
    response is created
    """
    await set_object_field(
        session=museum_session,
        object_id=1234567,
        name="ObjTestTxt", field_type="dataField",
        value="First line\nsecond line"
    )

    # Check that the expected response was constructed
    request = mock_museumplus.requests[0]

    assert request["method"] == "PUT"
    assert request["url"] == "/module/Object/1234567/ObjTestTxt"

    xml = lxml.etree.fromstring(request["content"])
    module_item = xml.find(
        f"{{{ZETCOM_NS}}}modules//"
        f"{{{ZETCOM_NS}}}moduleItem[@id='1234567']"
    )
    assert module_item.find(
        f"{{{ZETCOM_NS}}}dataField[@name='ObjTestTxt']"
    ) is not None
    assert module_item.find(
        f"{{{ZETCOM_NS}}}dataField[@name='ObjTestTxt']"
        f"{{{ZETCOM_NS}}}value"
    ).text == "First line\nsecond line"


@pytest.mark.asyncio
async def test_set_object_field_non_existent(museum_session, mock_museumplus):
    """
    Test updating a non-existent Object; this should raise an exception
    """
    with pytest.raises(ClientResponseError) as exc:
        await set_object_field(
            session=museum_session,
            object_id=999999,
            name="ObjTestTxt", field_type="dataField",
            value="First line\nsecond line"
        )

    assert exc.value.status == 404


@pytest.mark.asyncio
async def test_add_preservation_event_invalid_json(
        monkeypatch, museum_package):
    """
    Try adding a new preservation event when the currently stored data
    in MuseumPlus is invalid
    """
    async def mock_get_object_field(session, object_id, name):
        return "invalid json"

    monkeypatch.setattr(
        "passari.museumplus.fields.get_object_field",
        mock_get_object_field
    )

    with pytest.raises(ValueError) as exc:
        await add_preservation_event(museum_package, status="accepted")

    assert "Could not decode MuseumPlus preservation log entries" in str(exc)
