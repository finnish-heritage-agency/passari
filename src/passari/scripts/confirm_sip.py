"""
Confirm a SIP as either having been accepted or rejected in the digital
preservation service
"""
import shutil
from pathlib import Path

import click

from passari.config import CONFIG
from passari.dpres.package import MuseumObjectPackage
from passari.museumplus.fields import add_preservation_event
from passari.scripts.utils import async_run
from passari.utils import debugger_enabled


async def confirm_sip(
        package_dir, archive_dir, object_id: int,
        status: str, sip_id: str = None):
    """
    Confirm SIP (whether it was accepted or rejected) by copying
    the logs and ingest report into an archival directory

    :param package_dir: Path to directory containing objects under processing
    :param archive_dir: Path to directory containing logs for processed SIPs
    :param object_id: Object ID of the object to process
    :param status: Status of the object in the preservation service,
                   either "accepted" or "rejected"
    :param sip_id: Optional SIP ID used to generate multiple SIPs
                   from the same object version
    """
    if status not in ("accepted", "rejected"):
        raise ValueError(f"{status} is not a valid status")

    museum_package = await MuseumObjectPackage.from_path(
        path=package_dir / str(object_id), sip_id=sip_id
    )
    museum_package.copy_log_files_to_archive(archive_dir)

    # Add preservation event to MuseumPlus if enabled
    if CONFIG["museumplus"].get("add_log_entries", True):
        await add_preservation_event(
            museum_package=museum_package,
            status=status
        )

    # Remove the museum object directory
    shutil.rmtree(museum_package.path)

    print(f"Finished confirming SIP {museum_package.sip_filename}")


@click.command()
@click.option(
    "--package-dir",
    help="Directory used to process and store the objects",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=Path.home() / "MuseumObjects"
)
@click.option(
    "--archive-dir",
    help="Directory used to archive preservation reports and logs",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=Path.home() / "MuseumObjectArchive"
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
    "--status",
    help="Whether the package was accepted or rejected by the DPRES service",
    type=click.Choice(["accepted", "rejected"]),
    required=True
)
@click.argument("object_id", nargs=1)
def cli(package_dir, archive_dir, object_id, status, debug, sip_id):
    main(package_dir, archive_dir, object_id, status, debug, sip_id)


def main(
        package_dir, archive_dir, object_id, status, debug=False, sip_id=None):
    package_dir = Path(package_dir)
    archive_dir = Path(archive_dir)

    with debugger_enabled(debug):
        return async_run(
            confirm_sip(
                package_dir=package_dir,
                archive_dir=archive_dir,
                object_id=object_id,
                status=status,
                sip_id=sip_id
            )
        )


if __name__ == "__main__":
    cli()
