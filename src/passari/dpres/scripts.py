import asyncio
import datetime
import os
from pathlib import Path

import aiofiles
from passari.config import CONFIG
from passari.logger import logger

from subprocess import CalledProcessError


def get_virtualenv_environ(virtualenv_path):
    """
    Get the environment variables to use for running DPRES commands.
    This allows DPRES scripts to be launched from a separate Python
    virtualenv.
    """
    environ = os.environ.copy()
    virtualenv_path = Path(virtualenv_path)
    environ["PATH"] = "".join([
        str(virtualenv_path / "bin"), os.pathsep,
        environ["PATH"]
    ])
    environ["VIRTUAL_ENV"] = str(virtualenv_path)

    return environ


async def run_command(
        cmd: list, cwd: str = None, log_path=None, environ=None) -> str:
    """
    Run a command.
    If 'log_path' is provided, stdout and stderr will be written to this
    location regardless of the end result.

    :raises subprocess.CalledProcessError: If the command returned an error

    :returns: Command stdout
    """
    if not environ:
        environ = os.environ.copy()

    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
        env=environ
    )
    stdout, stderr = await process.communicate()

    if log_path:
        async with aiofiles.open(log_path, "ab") as file_:
            now = datetime.datetime.now(datetime.timezone.utc)
            await file_.write(
                f"\n===COMMAND===\n{now.isoformat()}\n{cmd}".encode("utf-8")
            )
            await file_.write(b"\n===STDOUT===\n")
            await file_.write(stdout)
            await file_.write(b"\n===STDERR===\n")
            await file_.write(stderr)

    if process.returncode != 0:
        raise CalledProcessError(
            returncode=process.returncode,
            cmd=cmd,
            output=stdout,
            stderr=stderr
        )

    logger.debug(
        "Command %s completed.\nOUTPUT: %s\n",
        " ".join(cmd), stdout
    )

    return stdout.decode("utf-8")


async def run_dpres_command(cmd: list, cwd: str = None, log_path=None):
    """
    Run a command involving one of the commands in dpres-siptools.
    If 'log_path' is provided, stdout and stderr will be written to this
    location regardless of the end result.
    """
    if CONFIG["dpres"]["use_virtualenv"]:
        environ = get_virtualenv_environ(
            virtualenv_path=CONFIG["dpres"]["virtualenv_path"]
        )
    else:
        environ = None

    return await run_command(
        cmd=cmd, cwd=cwd, log_path=log_path, environ=environ
    )


async def extract_archive(path, destination_path, log_path=None):
    """
    Extract an archive to the given directory and delete the original
    archive afterwards
    """
    path = Path(path)

    if path.suffix.lower() == ".zip":
        return await run_command(
            cmd=["unzip", str(path), "-d", str(destination_path)],
            log_path=log_path
        )

    raise RuntimeError(f"Can't extract archive {path}")


async def import_object(
        path, base_path, workspace_path, identifier_type=None,
        identifier_value=None, **kwargs):
    """
    Import a file using dpres-siptools tool 'import-object'
    """
    args = [
        "import-object", "--base_path", str(base_path),
        "--workspace", str(workspace_path),
    ]

    if identifier_value:
        args += ["--identifier", identifier_type or "", identifier_value]

    args += [str(path)]

    return await run_dpres_command(args, **kwargs)


async def create_mix(path, base_path, workspace_path, **kwargs):
    """
    Create MIX image metadata using dpres-siptools tool 'create-mix'
    """
    return await run_dpres_command([
        "create-mix", "--base_path", str(base_path),
        "--workspace", str(workspace_path), str(path)
    ], **kwargs)


async def add_premis_event(
        base_path, workspace_path, event_type, event_datetime,
        event_detail, event_outcome, event_target=None,
        event_outcome_detail=None, **kwargs):
    """
    Add a PREMIS event using dpres-siptools tool 'premis-event'
    """
    args = [
        "premis-event", "--base_path", str(base_path),
        "--workspace", str(workspace_path),
        "--event_detail", event_detail, "--event_outcome", event_outcome,
        "--agent_name", "passari",
        # Agent type 'software' used per example in
        # http://digitalpreservation.fi/files/PAS-metatiedot-ja-aineiston-paketointi-1.7.0.pdf
        "--agent_type", "software"
    ]

    if event_target:
        args += ["--event_target", str(event_target)]
    if event_outcome_detail:
        args += ["--event_outcome_detail", event_outcome_detail]

    args += [event_type, event_datetime.isoformat()]

    return await run_dpres_command(args, **kwargs)


async def import_description(workspace_path, dmd_location, **kwargs):
    """
    Add metadata from an XML file using dpres-siptools tool
    'import-description'
    """
    return await run_dpres_command([
        "import-description", "--workspace", str(workspace_path),
        str(dmd_location)
    ], **kwargs)


async def compile_structmap(base_path, workspace_path, **kwargs):
    """
    Compile the SIP's structure map using dpres-siptools tool
    'compile-structmap'
    """
    return await run_dpres_command([
        "compile-structmap", "--workspace", str(workspace_path)
    ], **kwargs)


async def compile_mets(
        base_path, workspace_path, objid, contentid, organization_name,
        contract_id, create_date, modify_date, update=False, **kwargs):
    """
    Compile the METS for a SIP usign dpres-siptools tool 'compile-mets'
    """
    record_status = "submission"
    if update:
        record_status = "update"

    args = [
        "compile-mets", "--workspace", str(workspace_path),
        "--base_path", str(base_path),
        "--objid", objid,
        "--contentid", contentid,
        "--record_status", record_status,
        "--create_date", create_date.isoformat(),
        "--clean"
    ]

    if modify_date:
        args += ["--last_moddate", modify_date.isoformat()]

    args += [
        "ch",  # 'ch' stands for the Cultural Heritage METS profile
        organization_name, contract_id
    ]

    return await run_dpres_command(args, **kwargs)


async def sign_mets(workspace_path, sign_key_path, **kwargs):
    """
    Sign the METS for a SIP using the dpres-siptools tool 'sign-mets'
    """
    return await run_dpres_command([
        "sign-mets", "--workspace", str(workspace_path), str(sign_key_path)
    ], **kwargs)


async def compress(path, destination, **kwargs):
    """
    Compress the complete SIP into a TAR archive
    """
    return await run_dpres_command([
        "tar", "-cvvf", str(destination), "."
    ], cwd=str(path), **kwargs)
