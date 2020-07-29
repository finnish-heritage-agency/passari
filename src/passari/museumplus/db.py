import datetime
from pathlib import Path

import dateutil.parser
import lxml.etree

from passari.config import MUSEUMPLUS_URL
from passari.museumplus.settings import ZETCOM_NS
from passari.utils import retrieve_xml


class BaseMuseumModule:
    """
    Base class for MuseumPlus modules that implements properties
    that are common to all modules such as creation date and username
    """
    @property
    def created_date(self) -> datetime.datetime:
        try:
            value = self.etree.find(
                f"{{{ZETCOM_NS}}}modules//"
                f"{{{ZETCOM_NS}}}systemField[@name='__created']//"
                f"{{{ZETCOM_NS}}}value"
            ).text
        except AttributeError:
            return None

        # Timestamps returned by MuseumPlus are in UTC
        date = dateutil.parser.parse(value)
        return date.replace(tzinfo=datetime.timezone.utc)

    @property
    def created_user(self) -> str:
        try:
            return self.etree.find(
                f"{{{ZETCOM_NS}}}modules//"
                f"{{{ZETCOM_NS}}}systemField[@name='__createdUser']//"
                f"{{{ZETCOM_NS}}}value"
            ).text
        except AttributeError:
            return None

    @property
    def modified_date(self) -> datetime.datetime:
        """
        Return the modification date of the timestamp.

        This is used in the SIP filename
        """
        value = self.etree.find(
            f"{{{ZETCOM_NS}}}modules//"
            f"{{{ZETCOM_NS}}}systemField[@name='__lastModified']//"
            f"{{{ZETCOM_NS}}}value"
        ).text

        date = dateutil.parser.parse(value)
        return date.replace(tzinfo=datetime.timezone.utc)

    @property
    def identifier(self) -> str:
        """
        Return the numeric identifier for this object
        """
        return self.etree.find(
            f"{{{ZETCOM_NS}}}modules//"
            f"{{{ZETCOM_NS}}}moduleItem[@id]"
        ).attrib["id"]


class MuseumObject(BaseMuseumModule):
    """
    Museum object representing an object in the MuseumPlus database
    """
    def __init__(self, etree, session):
        """
        Create a MuseumObject from a parsed XML document and session

        :param etree: XML document parsed by lxml
        :param session: aiohttp.Session instance
        """
        self.etree = etree
        self.session = session

    def tostring(self) -> bytes:
        """
        Return the XML document as a bytestring that can be saved
        """
        return lxml.etree.tostring(
            self.etree, encoding="UTF-8", xml_declaration=True
        )

    async def close(self):
        """
        Close the underlying aiohttp session
        """
        await self.session.close()

    @property
    def sip_name(self) -> str:
        """
        Filename of the SIP sent to the Digital Preservation service.
        Includes the unique identifying object ID as well as a timestamp
        to differentiate versions of the same package.
        """
        timestamp = self.modified_date.strftime("%Y%m%d")

        return f"{timestamp}_Object_{self.object_id}"

    @property
    def object_id(self) -> str:
        return self.identifier

    @property
    def title(self) -> str:
        try:
            return self.etree.find(
                f"{{{ZETCOM_NS}}}modules//"
                f"{{{ZETCOM_NS}}}dataField[@name='ObjObjectTitleTxt']//"
                f"{{{ZETCOM_NS}}}value"
            ).text
        except AttributeError:
            return "N/A"

    @property
    def attachment_ids(self) -> list:
        module_items = self.etree.findall(
            f"{{{ZETCOM_NS}}}modules//"
            f"{{{ZETCOM_NS}}}moduleReference[@name='ObjMultimediaRef']//"
            f"{{{ZETCOM_NS}}}moduleReferenceItem"
        )

        return [
            int(module_item.attrib["moduleItemId"])
            for module_item in module_items
        ]

    @property
    def collection_activity_ids(self) -> list:
        module_items = self.etree.findall(
            f"{{{ZETCOM_NS}}}modules//"
            f"{{{ZETCOM_NS}}}moduleReference"
            f"[@name='ObjCollectionActivityRef']//"
            f"{{{ZETCOM_NS}}}moduleReferenceItem"
        )

        return [
            int(module_item.attrib["moduleItemId"])
            for module_item in module_items
        ]

    async def download_package(self, path, sip_id: str = None):
        """
        Download the object metadata and attachments to the given path

        :param path: Directory where the package will be downloaded to.
                     Directory is created if it doesn't exist already.
        :param sip_id: Optional SIP ID that allows multiple SIP archives
                       to be generated for the same version of the museum
                       object
        """
        from passari.dpres.package import MuseumObjectPackage
        path = Path(path)
        path.mkdir(exist_ok=True)

        museum_package = MuseumObjectPackage(
            path, museum_object=self, sip_id=sip_id
        )
        await museum_package.download_attachments()
        await museum_package.download_collection_activities()
        await museum_package.download_reports()
        museum_package.populate_files()

        return museum_package


class MuseumAttachment(BaseMuseumModule):
    """
    Museum attachment representing a Multimedia object in the MuseumPlus
    service
    """
    def __init__(self, etree):
        self.etree = etree

    @property
    def filename(self) -> str:
        try:
            return self.etree.find(
                f"{{{ZETCOM_NS}}}modules//"
                f"{{{ZETCOM_NS}}}dataField[@name='MulOriginalFileTxt']//"
                f"{{{ZETCOM_NS}}}value"
            ).text
        except AttributeError:
            # If the attachment doesn't have a filename, use a generated
            # name
            return f"Multimedia_{self.attachment_id}.attachment"

    @property
    def attachment_id(self) -> str:
        return self.identifier


class MuseumCollectionActivity(BaseMuseumModule):
    """
    Museum collection activity representing a CollectionActivity object
    in the MuseumPlus service
    """
    def __init__(self, etree):
        self.etree = etree

    @property
    def collection_activity_id(self) -> str:
        return self.identifier


def check_object_xml(xml):
    """
    Check that the XML document for an Object is complete, otherwise raise
    an IOError.

    This can happen if the MuseumPlus user has insufficient permissions, in
    which case truncated XML documents are downloaded.

    :raises IOError: If the document appears to be incomplete
    """
    # Count the fields besides systemFields. If there are none, the service
    # is likely returning truncated XML documents
    field_count = len(
        xml.xpath(
            "zetcom:modules"
            "//zetcom:moduleItem"
            "/zetcom:*[local-name() != 'systemField']",
            namespaces={"zetcom": ZETCOM_NS}
        )
    )

    if field_count == 0:
        raise IOError(
            "Received a truncated XML document. The MuseumPlus user probably "
            "has insufficient permissions."
        )


async def get_museum_object(session, object_id) -> MuseumObject:
    """
    Download XML document for an Object and deserialize it into a MuseumObject
    instance

    :raises IOError: If the document appears to be incomplete due to
                     insufficient permissions
    """
    xml = await retrieve_xml(
        session, f"{MUSEUMPLUS_URL}/module/Object/{object_id}"
    )
    # Check that the XML document is complete
    check_object_xml(xml)

    return MuseumObject(xml, session=session)
