"""
Validate and package a downloaded object into a SIP
"""
import asyncio
import datetime
from pathlib import Path

import click

from passari.dpres.package import MuseumObjectPackage
from passari.util import debugger_enabled, DateTimeType


async def create_sip(
        package_dir, object_id, sip_id, update=False,
        create_date: datetime.datetime = None,
        modify_date: datetime.datetime = None):
    """
    Create a SIP in the given directory for an object ID

    :param package_dir: Path to the directory containing objects under
                        processing
    :param object_id: Object ID of the object to process
    :param sip_id: Optional SIP ID used to generate multiple SIPs
                   from the same object version
    :param update: Whether to generate a SIP to update an object already
                   stored by the preservation service
    :param create_date: Creation date of the SIP to be generated.
                        When creating an update SIP, the creation date
                        of an earlier SIP should be used.
    :param modify_date: Modification date of the SIP to be generated.
                        Needed when creating an update SIP.
    """
    if not create_date:
        create_date = datetime.datetime.now(datetime.timezone.utc)

    # Retrieve already downloaded object
    museum_package = await MuseumObjectPackage.from_path(
        path=package_dir / str(object_id), sip_id=sip_id
    )
    await museum_package.generate_sip(
        update=update, create_date=create_date, modify_date=modify_date
    )
    await museum_package.close()

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
@click.option(
    "--sip-id",
    help=(
        "Optional SIP ID allowing multiple SIPs to be generated for the "
        "same package."
    ),
    type=str, default=None
)
@click.option(
    "--create-date",
    type=DateTimeType(),
    default=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    help=(
        "The creation date for the submission SIP in ISO 8601 format. "
        "This is not the same as the creation date "
        "for the underlying museum object! Using the same value later on for "
        "update SIPs is recommended."
    )
)
@click.option(
    "--modify-date",
    type=DateTimeType(),
    default=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    help=(
        "The creation date for the update SIP in ISO 8601 format. "
        "Use this with the --create-date and --update "
        "parameters to create an update SIP."
    )
)
@click.option(
    "--update", is_flag=True, default=False,
    help="Create an update SIP instead of a normal SIP"
)
@click.argument("object_id", nargs=1)
def cli(
        package_dir, object_id, update, sip_id, create_date, modify_date,
        debug):
    main(
        package_dir=package_dir,
        object_id=object_id,
        update=update,
        sip_id=sip_id,
        create_date=create_date,
        modify_date=modify_date,
        debug=debug
    )


def main(package_dir, object_id, update=False, create_date=None,
         modify_date=None, sip_id=None, debug=False):
    package_dir = Path(package_dir)

    loop = asyncio.get_event_loop()
    with debugger_enabled(debug):
        return loop.run_until_complete(
            create_sip(
                package_dir=package_dir, object_id=object_id, sip_id=sip_id,
                update=update, create_date=create_date, modify_date=modify_date
            )
        )


if __name__ == "__main__":
    cli()
