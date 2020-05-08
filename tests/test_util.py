import lxml.etree

from passari.museumplus.settings import ZETCOM_NS
from passari.util import get_xml_hash

DOCUMENT_A = b"""<?xml version="1.0" encoding="UTF-8"?>
<application xmlns="http://www.zetcom.com/ria/ws/module">
    <modules>
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
        </moduleItem>
    </modules>
</application>
"""
# Identical to A, but has more recent modification datetime
DOCUMENT_B = b"""<?xml version="1.0" encoding="UTF-8"?>
<application xmlns="http://www.zetcom.com/ria/ws/module">
    <modules>
        <moduleItem hasAttachments="false" id="100001" uuid="1713AFC83A9C49D2A4048E17B58B1ECB">
            <systemField dataType="Long" name="__id">
                <value>100001</value>
            </systemField>
            <systemField dataType="Timestamp" name="__lastModified">
                <value>2019-11-21 10:44:19.6</value>
                <formattedValue language="en">21.11.2018 10:44</formattedValue>
            </systemField>
            <systemField dataType="Timestamp" name="__created">
                <value>2018-10-21 10:44:19.6</value>
                <formattedValue language="en">21.10.2018 10:44</formattedValue>
            </systemField>
            <virtualField name="ObjObjectVrt">
                <value>Object 100001</value>
            </virtualField>
        </moduleItem>
    </modules>
</application>
"""
# Identical to A, but has a different UUID
DOCUMENT_C = b"""<?xml version="1.0" encoding="UTF-8"?>
<application xmlns="http://www.zetcom.com/ria/ws/module">
    <modules>
        <moduleItem hasAttachments="false" id="100001" uuid="2713AFC83A9C49D2A4048E17B58B1ECB">
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
        </moduleItem>
    </modules>
</application>
"""


def test_get_xml_hash():
    hashes = []
    for doc in (DOCUMENT_A, DOCUMENT_B, DOCUMENT_C):
        xml = lxml.etree.fromstring(doc)
        module_item = xml.find(f".//{{{ZETCOM_NS}}}moduleItem")
        hashes.append(
            get_xml_hash(
                module_item,
                volatile_field_queries=[
                    f"{{{ZETCOM_NS}}}systemField[@name='__lastModified']",
                    f"{{{ZETCOM_NS}}}systemField[@name='__lastModifiedUser']"
                ]
            )
        )

    # Documents A and B get the same hash despite the changed modification
    # timestamp, while document C gets its own hash
    assert hashes == [
        "22b2540ec757f7c55e3fc8661d81f2604e94aaff6e714e4544461624ee41e3c9",
        "22b2540ec757f7c55e3fc8661d81f2604e94aaff6e714e4544461624ee41e3c9",
        "ab259034d4e7ee3b7eb940b2625aef83008ad87c6dac2edcb11738561889ccba"
    ]
