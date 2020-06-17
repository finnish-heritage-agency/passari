import datetime

import lxml.etree

import pytest
from passari.config import CONFIG
from passari.museumplus.search import (ObjectSearchResponse,
                                       iterate_multimedia, iterate_objects)
from passari.museumplus.settings import ZETCOM_SEARCH_NS


@pytest.mark.asyncio
async def test_iterate_objects(museum_session, mock_museumplus):
    """
    Test iterating Object entries without filtering them by modification date
    """
    search_iter = iterate_objects(museum_session)
    results = []
    async for result in search_iter:
        results.append(result)

    assert len(results) == 6
    assert [
        result["id"] for result in results
    ] == ["100001", "100002", "100003", "100004", "100005", "100006"]

    assert results[0]["modified_date"] == datetime.datetime(
        2018, 11, 21, 10, 44, 19, 600000, tzinfo=datetime.timezone.utc
    )
    assert results[0]["created_date"] == datetime.datetime(
        2018, 10, 21, 10, 44, 19, 600000, tzinfo=datetime.timezone.utc
    )
    assert results[0]["title"] == "Object 100001"
    assert not results[0]["multimedia_ids"]
    assert results[0]["xml_hash"] == \
        "513288f245e74b9a0afe046373773e5757487d48ce7032196829073f0152c86b"

    # Second Object has references to two other attachments/Multimedia objects
    assert results[1]["multimedia_ids"] == [123456, 654321]

    # Third object has no creation or modification date
    assert not results[2]["created_date"]
    assert not results[2]["modified_date"]

    search_request = mock_museumplus.requests[0]["content"]
    search_xml = lxml.etree.fromstring(search_request)

    # Search request did *not* filter the results by default
    assert search_xml.find(f".//{{{ZETCOM_SEARCH_NS}}}sort")
    assert len(search_xml.findall(f".//{{{ZETCOM_SEARCH_NS}}}expert")) == 0


@pytest.mark.asyncio
async def test_iterate_objects_filter_modification_date(
        museum_session, mock_museumplus):
    """
    Test iterating Object entries that have been modified after the given
    date
    """
    search_iter = iterate_objects(
        museum_session,
        modify_date_gte=datetime.datetime(
            2020, 1, 2, 12, 0, 0, tzinfo=datetime.timezone.utc
        )
    )
    results = []
    async for result in search_iter:
        results.append(result)

    # The mocked MuseumPlus search API returns the same results regardless of
    # the search query
    assert len(results) == 6

    # Instead, inspect the generated search request body to check that it's
    # what we're expecting
    search_request = mock_museumplus.requests[0]["content"]
    search_xml = lxml.etree.fromstring(search_request)

    # Search request did *not* filter the results by default
    assert search_xml.find(f".//{{{ZETCOM_SEARCH_NS}}}sort")
    expert_elem = search_xml.find(f".//{{{ZETCOM_SEARCH_NS}}}expert")

    assert expert_elem.attrib["module"] == "Object"

    or_elems = expert_elem.findall(f"{{{ZETCOM_SEARCH_NS}}}or/*")
    gte_elem = or_elems[0]
    is_null_elem = or_elems[1]

    # Greater or equal clause has the correct date
    assert gte_elem.tag == f"{{{ZETCOM_SEARCH_NS}}}greaterEquals"
    assert gte_elem.attrib["fieldPath"] == "__lastModified"
    assert gte_elem.attrib["operand"] == "2020-01-02T12:00:00+00:00"

    assert is_null_elem.tag == f"{{{ZETCOM_SEARCH_NS}}}isNull"


@pytest.mark.asyncio
async def test_iterate_multimedia(museum_session, mock_museumplus):
    """
    Test iterating Multimedia entries without filtering them by modification
    date
    """
    search_iter = iterate_multimedia(museum_session)
    results = []
    async for result in search_iter:
        results.append(result)

    assert len(results) == 6
    assert [
        result["id"] for result in results
    ] == ["100001", "100002", "100003", "100004", "100005", "100006"]

    assert results[0]["modified_date"] == datetime.datetime(
        2018, 11, 21, 10, 44, 19, 600000, tzinfo=datetime.timezone.utc
    )
    assert results[0]["created_date"] == datetime.datetime(
        2018, 10, 21, 10, 44, 19, 600000, tzinfo=datetime.timezone.utc
    )
    assert results[0]["filename"] == "Multimedia1.obj"
    assert not results[0]["object_ids"]

    # Second Multimedia object doesn't have a filename and refers to
    # two other objects
    assert not results[1]["filename"]
    assert results[1]["object_ids"] == [123456, 654321]
    assert results[2]["filename"] == "Multimedia3.obj"

    # Third Multimedia object doesn't have a creation or modification date
    assert not results[2]["created_date"]
    assert not results[2]["modified_date"]


SEARCH_RESULTS = b"""<?xml version="1.0" encoding="UTF-8"?>
<application xmlns="http://www.zetcom.com/ria/ws/module">
  <modules>
    <module name="Object" totalSize="2">
      <moduleItem hasAttachments="false" id="100001" uuid="1713AFC83A9C49D2A4048E17B58B1ECB">
        <systemField dataType="Long" name="__id">
          <value>100001</value>
        </systemField>
        <systemField dataType="Timestamp" name="__lastModified">
          <value>2018-11-21 10:44:19.6</value>
          <formattedValue language="en">21.11.2018 10:44</formattedValue>
        </systemField>
        <systemField dataType="Timestamp" name="__created">
          <value>2018-10-21 10:44:19.6</value>
          <formattedValue language="en">21.10.2018 10:44</formattedValue>
        </systemField>
        <virtualField name="ObjObjectVrt">
            <value>Object 100001</value>
        </virtualField>
        <dataField name="PreservationNotes">
            <value>Preservation was successful. :)</value>
        </dataField>
      </moduleItem>
      <moduleItem hasAttachments="false" id="100001" uuid="1713AFC83A9C49D2A4048E17B58B1ECB">
        <systemField dataType="Long" name="__id">
          <value>100001</value>
        </systemField>
        <systemField dataType="Timestamp" name="__lastModified">
          <value>2018-11-21 10:44:19.6</value>
          <formattedValue language="en">21.11.2018 10:44</formattedValue>
        </systemField>
        <systemField dataType="Timestamp" name="__created">
          <value>2018-10-21 10:44:19.6</value>
          <formattedValue language="en">21.10.2018 10:44</formattedValue>
        </systemField>
        <virtualField name="ObjObjectVrt">
            <value>Object 100001</value>
        </virtualField>
        <dataField name="PreservationNotes">
               <value>Preservation was unsuccessful. :(</value>
        </dataField>
      </moduleItem>
    </module>
  </modules>
</application>
"""


def test_museum_search_response_hash(monkeypatch):
    """
    Test that the field for preservation history doesn't affect the
    hash returned in search results
    """
    monkeypatch.setitem(
        CONFIG["museumplus"], "object_preservation_field_name",
        "PreservationNotes"
    )
    monkeypatch.setitem(
        CONFIG["museumplus"], "object_preservation_field_type",
        "dataField"
    )

    xml = lxml.etree.fromstring(SEARCH_RESULTS)
    search_response = ObjectSearchResponse(xml)
    results = search_response.results

    # Hashes should be identical despite differences in the preservation field
    # and non-meaningful whitespace
    assert results[0]["xml_hash"] == \
        "39c6cf572b1a39d56843dd5e2dc27912021faf67959c9e12169ab703e39074c8"
    assert results[1]["xml_hash"] == \
        "39c6cf572b1a39d56843dd5e2dc27912021faf67959c9e12169ab703e39074c8"
