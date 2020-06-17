"""
Submit a SIP archive to the digital preservation service
"""
import asyncio
from pathlib import Path

import click
from passari.config import CONFIG
from passari.dpres.package import MuseumObjectPackage
from passari.dpres.ssh import connect_dpres_sftp
from passari.util import debugger_enabled


def submit_sip(package_dir, object_id: int, sip_id: str = None):
    """
    Submit SIP to the DPRES service

    :param package_dir: Path to directory containing objects under processing
    :param archive_dir: Path to directory containing logs for processed SIPs
    :param object_id: Object ID of the object to process
    :param sip_id: Optional SIP ID used to generate multiple SIPs
                   from the same object version
    """
    with connect_dpres_sftp() as sftp:
        museum_package = MuseumObjectPackage.from_path_sync(
            path=package_dir / str(object_id), sip_id=sip_id
        )
        # DPRES service won't process files with the suffix '.incomplete'
        temp_filename = f"{museum_package.sip_filename}.incomplete"
        dest_path = Path(CONFIG["ssh"]["home_path"]) / "transfer"

        print(f"Uploading to {dest_path / temp_filename}")
        sftp.put(
            museum_package.sip_archive_path,
            str(dest_path / temp_filename)
        )

        print("Renaming uploaded file")
        sftp.rename(
            str(dest_path / temp_filename),
            str(dest_path / museum_package.sip_filename)
        )

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
@click.argument("object_id", nargs=1)
def cli(package_dir, object_id, debug, sip_id):
    main(package_dir, object_id, debug, sip_id)


def main(package_dir, object_id, debug=False, sip_id=None):
    package_dir = Path(package_dir)

    with debugger_enabled(debug):
        return submit_sip(
            package_dir=package_dir, object_id=object_id, sip_id=sip_id
        )


if __name__ == "__main__":
    cli()
