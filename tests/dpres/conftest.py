from pathlib import Path

import pytest


@pytest.fixture(scope="function")
def package_dir(tmpdir):
    package_dir = Path(tmpdir) / "package"
    package_dir.mkdir(exist_ok=True)

    return package_dir


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def museum_package_factory(
        load_museum_object, mock_museumplus, package_dir):
    async def func(object_id, sip_id=None):
        museum_object = load_museum_object(object_id=object_id)
        museum_package = await museum_object.download_package(
            package_dir, sip_id=sip_id
        )
        return museum_package

    return func


@pytest.fixture(scope="function")
@pytest.mark.asyncio
async def museum_package(museum_package_factory):
    return await museum_package_factory("1234567")
