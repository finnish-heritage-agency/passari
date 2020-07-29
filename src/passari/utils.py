import asyncio
import contextlib
import datetime
import hashlib
from concurrent.futures import FIRST_EXCEPTION, ALL_COMPLETED

import dateutil.parser
import lxml.etree
from click.types import ParamType

import aiofiles
from passari.logger import logger


async def retrieve_xml(session, url: str):
    """
    Retrieve an XML document from the given URL and return the parsed
    XML document's root node
    """
    response = await session.get(
        url, headers={"Content-Type": "application/xml"}
    )
    response.raise_for_status()
    result = await response.read()

    return lxml.etree.fromstring(result)


async def post_xml(session, url: str, data: dict):
    """
    Retrieve an XML document from the given URL using a POST request
    and return the XML document's root node
    """
    response = await session.post(
        url, headers={"Content-Type": "application/xml"},
        data=data
    )
    response.raise_for_status()
    result = await response.read()

    return lxml.etree.fromstring(result)


async def retrieve_cached_xml(session, url: str, path):
    """
    Retrieve and deserialize XML using either of the two options:
    1. local filesystem path, if the XML file already exists
    2. URL, if the file doesn't already exist

    In the latter case, the file will be saved locally if the file doesn't
    exist.

    This function can be used for XML content that changes infrequently
    and doesn't need to be redownloaded each time
    """
    content = None

    try:
        async with aiofiles.open(path, "rb") as file_:
            content = await file_.read()
        logger.debug("XML document %s already exists", path)
    except FileNotFoundError:
        logger.debug("Downloading missing XML document %s", path)
        response = await session.get(
            url, headers={"Content-Type": "application/xml"}
        )
        response.raise_for_status()
        content = await response.read()

        async with aiofiles.open(path, "wb") as file_:
            await file_.write(content)

    return lxml.etree.fromstring(content)


async def gather_or_raise_first(*aws):
    """
    Wait and return a list of results for awaitables if all succeed.
    If any of the tasks fails, cancel all remaining tasks and raise the first
    encountered exception and discard the rest.

    This is used when we only need to handle one exception from possibly
    multiple exceptions.
    """
    if not aws:
        return []

    tasks = [asyncio.ensure_future(aw) for aw in aws]

    # Wait until all tasks succeed or one of them fails
    await asyncio.wait(tasks, return_when=FIRST_EXCEPTION)

    failed_tasks = [task for task in tasks if task.exception() is not None]

    if failed_tasks:
        # One of the tasks failed, cancel all tasks and raise the first
        # exception we find
        for task in tasks:
            if not task.done():
                task.cancel()

        # Ensure all tasks are completed including cancellations
        await asyncio.wait(tasks, return_when=ALL_COMPLETED)

        # Log all the exceptions
        excs = [
            task.exception() for task in tasks if task.exception() is not None
        ]

        logger.warning(
            "'gather_or_raise_first' caught %d exceptions.", len(excs)
        )
        for exc in excs:
            logger.warning("Caught: %s", str(exc))

        raise failed_tasks[0].exception()

    # All succeeded, return the results
    return [task.result() for task in tasks]


def unix_timestamp_to_datetime(timestamp: int):
    """
    Convert an UNIX timestamp in seconds to a `datetime.datetime` object
    """
    timestamp = int(timestamp)

    date = datetime.datetime.utcfromtimestamp(timestamp)
    date.replace(tzinfo=datetime.timezone.utc)

    return date


def get_xml_hash(
        root: lxml.etree.Element,
        volatile_field_queries: list = None,
        base_query: str = ".") -> str:
    """
    Calculate a hash for an XML document. Given volatile field names
    will be stripped out of the XML document before calculation.

    This makes it possible to detect changes for XML documents while ignoring
    fields like "last modification datetime" that shouldn't trigger an update.
    """
    if not volatile_field_queries:
        volatile_field_queries = []

    for field_query in volatile_field_queries:
        xpath_query = f"{base_query}//{field_query}"

        for elem in root.findall(xpath_query):
            elem.getparent().remove(elem)

    data = lxml.etree.tostring(
        root,
        method="c14n",  # Use Canonical XML to make output deterministic
        with_comments=False, strip_text=True
    )
    hash_ = hashlib.sha256(data).hexdigest()

    return hash_


@contextlib.contextmanager
def debugger_enabled(enable: bool = True):
    """
    Context manager to enable post-mortem debugger

    :param bool enable: Whether to enable debugger on exception
    """
    try:
        yield
    except Exception:
        if enable:
            import pdb
            import traceback
            traceback.print_exc()
            pdb.post_mortem()
        else:
            raise


class DateTimeType(ParamType):
    """
    Click parameter that parses ISO 8601 strings using dateutil.parser.parse.

    This is needed to support ISO 8601 strings with timezone offsets
    in Python 3.6.
    """
    name = "datetime"

    def convert(self, value, param, ctx):
        try:
            return dateutil.parser.isoparse(value)
        except ValueError:
            self.fail("invalid ISO 8601 string")
