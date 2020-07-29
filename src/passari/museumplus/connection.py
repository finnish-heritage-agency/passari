import os
import time
from pathlib import Path
from urllib.parse import urlparse

from pkg_resources import DistributionNotFound, get_distribution

import aiohttp
from filelock import FileLock
from passari.config import CONFIG, MUSEUMPLUS_URL
from passari.logger import logger
from passari.museumplus.settings import ZETCOM_SESSION_NS
from passari.utils import retrieve_xml

# Session key will be regenerated after this many seconds if no requests
# have been for this long
SESSION_KEY_REGENERATE_TIMEOUT = 600

try:
    PASSARI_VERSION = get_distribution("passari").version
except DistributionNotFound:
    PASSARI_VERSION = "unknown"


USER_AGENT = (
    f"passari/{PASSARI_VERSION} "
    f"(github.com/finnish-heritage-agency/passari)"
)


def get_session_key_file_path() -> Path:
    """
    Return the path to a host-specific session key file
    """
    museumplus_host = urlparse(MUSEUMPLUS_URL).netloc

    # Use a different file for each MuseumPlus host
    path = (
        Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
        / "passari"
        / f"{museumplus_host}.session"
    )
    return path


async def refresh_session_key(session, trace_config_ctx, params):
    """
    Refresh the session key after the first response chunk is read after
    a successful request
    """
    response_started = getattr(trace_config_ctx, "response_started", False)

    if not response_started:
        # This is the first response chunk we've received; refresh
        # the session key file. This signal is not fired when receiving the
        # headers, so as long as we call `response.raise_for_status()` before
        # `await response.read()`, non-successful HTTP requests will not
        # refresh the session key file and potentially cause the session to
        # expire server-side while appearing to be alive on the client-side.
        #
        # The method is synchronous, but should be fast enough not to interrupt
        # the event loop too much.
        path = get_session_key_file_path()
        path.touch()

        trace_config_ctx.response_started = True


async def generate_museum_session_key(previous_key=None) -> str:
    """
    Generate a new session key for the MuseumPlus service and return it

    :returns: New session key
    """
    key_path = get_session_key_file_path()
    lock = FileLock(key_path.with_suffix(".lock"))

    with lock:
        # We got the lock but it's possible that the previous lock owner
        # generated the session key just before us
        try:
            session_key = key_path.read_text()
        except FileNotFoundError:
            session_key = None

        if session_key != previous_key:
            # The key was just regenerated, no need to regenerate it
            return session_key

        logger.info("Regenerating session key %s", str(key_path))

        # Key hasn't changed, so we need to generate a new one
        user = CONFIG["museumplus"]["username"]
        password = CONFIG["museumplus"]["password"]

        session = aiohttp.ClientSession(
            headers={
                "User-Agent": USER_AGENT
            },
            auth=aiohttp.BasicAuth(
                login=f"user[{user}]", password=f"password[{password}]"
            )
        )
        xml = await retrieve_xml(session, f"{MUSEUMPLUS_URL}/session")
        session_key = xml.find(
            f"{{{ZETCOM_SESSION_NS}}}session//"
            f"{{{ZETCOM_SESSION_NS}}}key"
        ).text

        key_path.write_text(session_key)

        await session.close()

        return session_key


async def get_museum_session_key() -> str:
    """
    Retrieve a session key for the MuseumPlus service, generating a new
    one if necessary.

    :returns: Session key
    """
    # We might have an active session key stored locally.
    key_path = get_session_key_file_path()
    try:
        session_time = key_path.stat().st_mtime
        session_key = key_path.read_text()
    except FileNotFoundError:
        # Create the parent directories and/or file if they don't exist
        os.makedirs(key_path.parent, exist_ok=True)
        session_time = time.time()
        session_key = await generate_museum_session_key(previous_key=None)

    # Regenerate a session key if it *could* have expired.
    # This is done because the alternative is to test the session key for
    # validity each time a session is created, and this would create
    # more useless requests than regenerating a session key after the worker
    # has stayed dormant for a while; a far more unlikely scenario.
    maybe_expired = time.time() - SESSION_KEY_REGENERATE_TIMEOUT > session_time

    if maybe_expired:
        session_key = await generate_museum_session_key(
            previous_key=session_key
        )

    return session_key


async def get_museum_session() -> aiohttp.ClientSession:
    """
    Return an aiohttp session to use for requests to the MuseumPlus service

    This ensures that credentials are used and amount of active connections
    is limited.

    Generating a museum session should be postponed until absolutely necessary;
    this allows passari to accurately determine when the previous
    session key has expired and a new one should be generated.
    """
    user = CONFIG["museumplus"]["username"]

    session_key = await get_museum_session_key()

    # Refresh the session key file after every successful request to indicate
    # that the session key still works
    trace_config = aiohttp.TraceConfig()
    trace_config.on_response_chunk_received.append(refresh_session_key)

    return aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=3),
        timeout=aiohttp.ClientTimeout(
            # Allow up to a 10 minute gap between data segments.
            # Without the parameter set the session will wait forever
            # for data that will never arrive if MuseumPlus hangs for
            # whatever reason
            sock_connect=600,
            sock_read=600
        ),
        trace_configs=[trace_config],
        auth=aiohttp.BasicAuth(
            login=f"user[{user}]", password=f"session[{session_key}]"
        ),
        headers={
            "User-Agent": USER_AGENT
        }
    )
