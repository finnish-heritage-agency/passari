import os
import time

import pytest
from passari.museumplus.connection import get_museum_session


@pytest.mark.asyncio
async def test_museum_session_key_generated(mock_museumplus, cache_dir):
    """
    Test that creating a MuseumPlus session causes a session key file to be
    created
    """
    session = await get_museum_session()

    # Find the session file. The port is random
    key_path = next((cache_dir / "passari").glob("127.0.0.1*.session"))
    # File is created with the session key
    assert key_path.read_text("utf-8") == "fakefakefakefakefakefakefakefake"

    await session.close()


@pytest.mark.asyncio
async def test_museum_session_key_regenerated(mock_museumplus, cache_dir):
    """
    Test that MuseumPlus session key file is regenerated after remaining
    unused for a certain amount of time
    """
    session = await get_museum_session()
    await session.close()

    key_path = next((cache_dir / "passari").glob("127.0.0.1*.session"))
    key_path.write_text("kafekafekafekafekafekafekafekafe")

    # Creating new session immediately will not change the contents
    session = await get_museum_session()
    await session.close()

    assert key_path.read_text() == "kafekafekafekafekafekafekafekafe"

    os.utime(key_path, (time.time() - 86400, time.time() - 86400))

    # Session key is now old enough and will be regenerated
    session = await get_museum_session()
    await session.close()

    assert key_path.read_text() == "fakefakefakefakefakefakefakefake"
