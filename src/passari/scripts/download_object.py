"""
Download an object from a MuseumPlus instance
"""
import asyncio
from pathlib import Path

import click
from passari.museumplus.connection import get_museum_session
from passari.museumplus.db import get_museum_object
from passari.util import debugger_enabled
from passari.dpres.package import MuseumObjectPackage


async def download_object(
        package_dir, object_id: int,
        sip_id: str = None) -> MuseumObjectPackage:
    """
    Download an object from MuseumPlus and return a MuseumObjectPackage
    instance

    :param package_dir: Path to directory containing objects under processing
    :param object_id: Object ID of the object to process
    :param sip_id: SIP ID to allow creating multiple SIPs for the same
                   museum object. While optional at this stage, providing
                   this parameter ensures the returned MuseumObjectPackage
                   has the correct file name.

                   This is necessary when calling this function from a
                   workflow job.
    """
    session = await get_museum_session()
    # 1. Retrieve object
    print(f"Retrieving object {object_id}")
    museum_object = await get_museum_object(
        session=session, object_id=object_id)
    print(f"Downloading object {object_id}")
    museum_package = await museum_object.download_package(
        package_dir / str(object_id), sip_id=sip_id
    )
    await museum_object.close()

    return museum_package


@click.command()
@click.option(
    "--package-dir",
    help="Directory used to process and store the objects",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=Path.home() / "MuseumObjects"
)
@click.option(
    "--debug/--no-debug", default=False, envvar="MUSEUMPLUS_DEBUG",
    help=(
        "Enable debug mode. Any unhandled exception will launch a debugger."
    )
)
@click.argument("object_id", nargs=1)
def cli(package_dir, object_id, debug):
    main(package_dir=package_dir, object_id=object_id, debug=debug)


def main(package_dir, object_id, sip_id=None, debug=False):
    """
    Script entrypoint.

    In addition to CLI arguments, the function accepts the 'sip_id' parameter
    to ensure that the returned MuseumObjectPackage has the correct
    filename
    """
    package_dir = Path(package_dir)

    loop = asyncio.get_event_loop()
    with debugger_enabled(debug):
        return loop.run_until_complete(
            download_object(
                package_dir=package_dir, object_id=object_id, sip_id=sip_id
            )
        )


if __name__ == "__main__":
    cli()
