import datetime

import dateutil.parser
import lxml.etree as ET

from passari.config import CONFIG, MUSEUMPLUS_URL
from passari.logger import logger
from passari.museumplus.settings import ZETCOM_NS, ZETCOM_SEARCH_NS
from passari.utils import get_xml_hash, post_xml

# Search template to retrieve objects in an ascending order from oldest to
# newest.
SEARCH_TEMPLATE = """
<?xml version="1.0" encoding="UTF-8"?>
<application xmlns="http://www.zetcom.com/ria/ws/module/search" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.zetcom.com/ria/ws/module/search http://docs.zetcom.com/ws/module/search/search_1_4.xsd">
  <modules>
    <module name="{module_name}">
      <search limit="{limit}" offset="{offset}">
        <sort>
          <field fieldPath="__id" direction="Ascending"/>
        </sort>
      </search>
    </module>
  </modules>
</application>"""[1:]  # Skip the first newline to make XML valid


def format_search_request(
        module_name, limit, offset, modify_date_gte=None) -> bytes:
    """
    Return a XML-formatted request body to perform the given search
    """
    data = SEARCH_TEMPLATE.format(
        module_name=module_name, limit=limit, offset=offset
    )
    xml = ET.fromstring(data.encode("utf-8"))

    if modify_date_gte:
        # Add the search filter if necessary
        search_elem = xml.find(f".//{{{ZETCOM_SEARCH_NS}}}search")
        expert_elem = ET.SubElement(search_elem, "expert")
        expert_elem.attrib["module"] = module_name

        or_elem = ET.SubElement(expert_elem, "or")
        or_elem.append(
            ET.Element(
                "greaterEquals",
                fieldPath="__lastModified", operand=modify_date_gte.isoformat()
            )
        )
        or_elem.append(ET.Element("isNull", fieldPath="__lastModified"))

    return ET.tostring(xml)


class MuseumSearchResponse:
    """
    Base class for parsing search results.

    This should be subclassed for each search type.
    """
    def __init__(self, etree):
        self.etree = etree

    def module_item_to_result(self, module_item):
        raise NotImplementedError()

    @property
    def results(self):
        module_items = self.etree.findall(
            f"{{{ZETCOM_NS}}}modules//"
            f"{{{ZETCOM_NS}}}moduleItem"
        )

        return [
            self.module_item_to_result(module_item)
            for module_item in module_items
        ]


class ObjectSearchResponse(MuseumSearchResponse):
    """
    Class for parsing Object search results
    """
    def module_item_to_result(self, module_item):
        object_id = module_item.find(
            f"{{{ZETCOM_NS}}}systemField[@name='__id']//"
            f"{{{ZETCOM_NS}}}value"
        ).text

        try:
            title = module_item.find(
                f"{{{ZETCOM_NS}}}virtualField[@name='ObjObjectVrt']//"
                f"{{{ZETCOM_NS}}}value"
            ).text
        except AttributeError:
            title = None

        try:
            modified_date = module_item.find(
                f"{{{ZETCOM_NS}}}systemField[@name='__lastModified']//"
                f"{{{ZETCOM_NS}}}value"
            ).text
            modified_date = dateutil.parser.parse(modified_date)
            modified_date = modified_date.replace(tzinfo=datetime.timezone.utc)
        except AttributeError:
            # Some objects don't actually have a creation and modification
            # dates
            modified_date = None

        try:
            created_date = module_item.find(
                f"{{{ZETCOM_NS}}}systemField[@name='__created']//"
                f"{{{ZETCOM_NS}}}value"
            ).text
            created_date = dateutil.parser.parse(created_date)
            created_date = created_date.replace(tzinfo=datetime.timezone.utc)
        except AttributeError:
            created_date = None

        multimedia_ids = [
            int(module.attrib["moduleItemId"])
            for module in module_item.findall(
                f".//{{{ZETCOM_NS}}}moduleReference[@name='ObjMultimediaRef']//"
                f"{{{ZETCOM_NS}}}moduleReferenceItem"
            )
        ]

        # Calculate the XML metadata hash for Object, while ignoring
        # some volatile fields that we will change during the preservation
        # process
        volatile_field_queries = [
            f"{{{ZETCOM_NS}}}systemField[@name='__lastModified']",
            f"{{{ZETCOM_NS}}}systemField[@name='__lastModifiedUser']"
        ]

        if CONFIG.get("museumplus", {}).get("object_preservation_field_name"):
            field_name = (
                CONFIG["museumplus"]["object_preservation_field_name"]
            )
            field_type = (
                CONFIG["museumplus"]["object_preservation_field_type"]
            )

            volatile_field_queries.append(
                f"{{{ZETCOM_NS}}}{field_type}[@name='{field_name}']"
            )

        xml_hash = get_xml_hash(
            module_item,
            volatile_field_queries=volatile_field_queries
        )

        return {
            "id": object_id,
            "title": title,
            "modified_date": modified_date,
            "created_date": created_date,
            "multimedia_ids": multimedia_ids,
            "xml_hash": xml_hash
        }


class MultimediaSearchResponse(MuseumSearchResponse):
    """
    Class for parsing Multimedia search results
    """
    def module_item_to_result(self, module_item) -> dict:
        """
        Convert a module's XML element to a result dict
        """
        multimedia_id = module_item.find(
            f"{{{ZETCOM_NS}}}systemField[@name='__id']//"
            f"{{{ZETCOM_NS}}}value"
        ).text

        try:
            filename = module_item.find(
                f"{{{ZETCOM_NS}}}dataField[@name='MulOriginalFileTxt']//"
                f"{{{ZETCOM_NS}}}value"
            ).text
        except AttributeError:
            filename = None

        try:
            modified_date = module_item.find(
                f"{{{ZETCOM_NS}}}systemField[@name='__lastModified']//"
                f"{{{ZETCOM_NS}}}value"
            ).text
            modified_date = dateutil.parser.parse(modified_date)
            modified_date = modified_date.replace(tzinfo=datetime.timezone.utc)
        except AttributeError:
            modified_date = None

        try:
            created_date = module_item.find(
                f"{{{ZETCOM_NS}}}systemField[@name='__created']//"
                f"{{{ZETCOM_NS}}}value"
            ).text
            created_date = dateutil.parser.parse(created_date)
            created_date = created_date.replace(tzinfo=datetime.timezone.utc)
        except AttributeError:
            created_date = None

        # In Multimedia results, the moduleReference is wrapped like this:
        # <composite>
        #   <compositeItem>
        #     <moduleReference>...</moduleReference>
        #   </compositeItem>
        # </composite>
        # In Object results, the moduleReference appears as-is, without any
        # other elements around it.
        # Use a more coarse query to catch both cases
        object_ids = [
            int(module.attrib["moduleItemId"])
            for module in module_item.findall(
                f".//{{{ZETCOM_NS}}}moduleReference[@name='MulObjectRef']//"
                f"{{{ZETCOM_NS}}}moduleReferenceItem"
            )
        ]

        # The "last modification" fields don't need to be ignored during
        # hash calculation, since we don't update the MuseumPlus fields.
        # They're also probably the only way we can determine if the
        # underlying attachment may have changed
        xml_hash = get_xml_hash(module_item)

        return {
            "id": multimedia_id,
            "filename": filename,
            "modified_date": modified_date,
            "created_date": created_date,
            "object_ids": object_ids,
            "xml_hash": xml_hash
        }


async def _iterate_search(
        session, response_cls, module_name: str, offset: int = 0,
        limit: int = 50, modify_date_gte=None):
    """
    Return an async iterator that can be used to iterate given amount of
    MuseumPlus modules of the given type

    .. note::

        Use :func:`iterate_multimedia` and :func:`iterate_objects` instead
        of this function for iterating modules of those types.

    :param session: MuseumPlus aiohttp session
    :param response_cls: Response class used to parse the search results
    :param module_name: Module name used by the MuseumPlus service
    :param offset: Offset for search results
    :param limit: How many results to return at most
    """
    result_count = 0

    while True:
        # Every request for 500 search results takes around 7 seconds
        # This means that a database with around 868,000 objects takes around
        # 3.5 hours to crawl, assuming no other overhead
        search_request = format_search_request(
            module_name=module_name, offset=offset, limit=limit,
            modify_date_gte=modify_date_gte
        )
        search_result = await post_xml(
            session,
            url=f"{MUSEUMPLUS_URL}/module/{module_name}/search",
            data=search_request
        )
        search_result = response_cls(search_result)
        results = search_result.results

        if not results:
            logger.info("Iterated all %d results", result_count)
            break

        for result in results:
            result_count += 1
            yield result

        offset += limit


async def iterate_multimedia(
        session, offset: int = 0, limit: int = 50, modify_date_gte=None):
    """
    Iterate all the Multimedia modules in the MuseumPlus database starting
    from the given offset

    :param session: aiohttp session used to retrieve the results
    :param int offset: The offset for search results. Default is 0, meaning
                      no results are skipped.
    :param int limit: How many results to retrieve from the server at the time.
    :param modify_date_gte: If provided, only iterate entries that have been
                            updated after this date.
    """
    iterator = _iterate_search(
        response_cls=MultimediaSearchResponse,
        module_name="Multimedia",
        session=session,
        offset=offset,
        limit=limit,
        modify_date_gte=modify_date_gte
    )
    async for entry in iterator:
        yield entry


async def iterate_objects(
        session, offset: int = 0, limit: int = 50, modify_date_gte=None):
    """
    Iterate all the Object modules in the MuseumPlus database starting from
    the given offset

    :param session: aiohttp session used to retrieve the results
    :param int offset: The offset for search results. Default is 0, meaning
                      no results are skipped.
    :param int limit: How many results to retrieve from the server at the time.
    :param modify_date_gte: If provided, only iterate entries that have been
                            updated after this date.
    """
    iterator = _iterate_search(
        response_cls=ObjectSearchResponse,
        module_name="Object",
        session=session,
        offset=offset,
        limit=limit,
        modify_date_gte=modify_date_gte
    )
    async for entry in iterator:
        yield entry
