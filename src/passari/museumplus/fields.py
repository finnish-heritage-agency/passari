import datetime
import json

from lxml.etree import Element, fromstring, tostring

from passari.config import CONFIG, MUSEUMPLUS_URL
from passari.museumplus.settings import ZETCOM_NS
from passari.utils import retrieve_xml


async def get_object_field(session, object_id: int, name: str):
    """
    Get the value of a single Object field

    :param session: aiohttp.Session instance
    :param object_id: ID of the Object to retrieve
    :param name: Field to retrieve

    :returns: Value of the field as string if it exists, None otherwise
    """
    # Retrieving the entire document seems to be the only option
    xml = await retrieve_xml(
        session, f"{MUSEUMPLUS_URL}/module/Object/{object_id}"
    )
    try:
        return xml.find(
            f"{{{ZETCOM_NS}}}modules//"
            f"{{{ZETCOM_NS}}}moduleItem[@id='{object_id}']"
            f"{{{ZETCOM_NS}}}*[@name='{name}']"
            f"{{{ZETCOM_NS}}}value"
        ).text
    except AttributeError:
        return None


UPDATE_FIELD_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8"?>
<application xmlns="http://www.zetcom.com/ria/ws/module">
  <modules>
    <module name="Object">
      <moduleItem id="{object_id}">
      </moduleItem>
    </module>
</modules>
</application>
"""[1:]


async def set_object_field(
        session, object_id: int, name: str, field_type: str,
        value: str):
    """
    Set the value of a single Object field. Value will be created if the
    field does not exist already.

    :param session: aiohttp.Session instance
    :param object_id: ID of the Object to retrieve
    :param name: Field name to retrieve
    :param field_type: Field type (eg. "dataField")
    :param value: Value to set
    """
    root = fromstring(
        UPDATE_FIELD_TEMPLATE.format(object_id=object_id).encode("utf-8")
    )

    module_elem = root.find(
        f"{{{ZETCOM_NS}}}modules//{{{ZETCOM_NS}}}moduleItem"
    )

    field_elem = Element(field_type)
    field_elem.attrib["name"] = name

    value_elem = Element("value")
    value_elem.text = value

    field_elem.append(value_elem)
    module_elem.append(field_elem)

    data = tostring(root, encoding="utf-8", xml_declaration=True)

    response = await session.put(
        f"{MUSEUMPLUS_URL}/module/Object/{object_id}/{name}",
        headers={"Content-Type": "application/xml"},
        data=data
    )
    response.raise_for_status()

    return True


async def add_preservation_event(museum_package, status):
    """
    Add a preservation event to the MuseumPlus service
    """
    event = {
        "filename": museum_package.sip_filename,
        "status": status,
        "object_modify_date": museum_package.museum_object.modified_date.isoformat(),
        "date": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    field_name = CONFIG["museumplus"]["object_preservation_field_name"]
    field_type = CONFIG["museumplus"]["object_preservation_field_type"]

    # Get the current events
    events = await get_object_field(
        session=museum_package.session,
        object_id=museum_package.museum_object.object_id,
        name=field_name
    )

    if not events:
        events = "[]"

    try:
        events = json.loads(events)
    except json.decoder.JSONDecodeError as exc:
        raise ValueError(
            "Could not decode MuseumPlus preservation log entries. The "
            "preservation field's content might be corrupted."
        ) from exc

    events.append(event)

    # Update the preservation events
    await set_object_field(
        session=museum_package.session,
        object_id=museum_package.museum_object.object_id,
        name=field_name,
        field_type=field_type,
        value=json.dumps(events)
    )
