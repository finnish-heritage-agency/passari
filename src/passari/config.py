import os
from pathlib import Path

import click
import toml


def get_config(app_name: str, config_name: str, default_config: str):
    """
    Try retrieving the configuration file content from the following sources
    in the following order:
    1. <APP_NAME>_CONFIG_PATH env var, if provided
    2. '/etc/<app_name>/<config_name>' path
    3. Local configuration directory as determined by `click.get_app_dir()`

    In addition, the default config will be written to source 3 in case no
    config sources are available.

    :param app_name: Application name used for the configuration directory name
    :param config_name: Configuration file name
    :param default_config: Default configuration as TOML-formatted string
    """
    env_name = f"{app_name.upper().replace('-', '_')}_CONFIG_PATH"
    if os.environ.get(env_name):
        return Path(os.environ[env_name]).read_text()

    system_path = Path("/etc") / app_name / config_name
    if system_path.is_file():
        return system_path.read_text()

    local_path = Path(click.get_app_dir(app_name)) / config_name
    if local_path.is_file():
        return local_path.read_text()

    local_path.parent.mkdir(exist_ok=True, parents=True)
    local_path.write_text(default_config)
    return default_config


DEFAULT_CONFIG = f"""
[logging]
# different logging levels:
# 50 = critical
# 40 = error
# 30 = warning
# 20 = info
# 10 = debug
level=10

[mets]
# Organization name used in PREMIS events
organization_name='ORGANIZATION NAME HERE'
# Contract ID used for DPRES REST API and in PREMIS events
contract_id='12345678-f00d-d00f-a4b7-010a184befdd'

[sign]
# Path to the key used to sign the METS
key_path='{Path(__file__).parent / "data" / "test_rsa_keys.crt"}'

[ssh]
host=''
port='22'
username=''
private_key=''
home_path=''

[museumplus]
# MuseumPlus instance URL ending with '/ria-ws/application'
url=''

# Template ID used for generating the LIDO XML report
lido_report_id='45005'

# Field used for storing the preservation history for an object
# Needs to have the 'Clob' data type
object_preservation_field_name=''
object_preservation_field_type='dataField'

# Whether to update MuseumPlus log field with preservation events
add_log_entries=true
username=''
password=''

[dpres]
# Virtualenv settings for dpres-siptools.
# These allow dpres-siptools to be installed separately
# from passari.
use_virtualenv=false
virtualenv_path=''
"""

CONFIG = toml.loads(
    get_config("passari", "config.toml", DEFAULT_CONFIG)
)

ORGANIZATION_NAME = CONFIG["mets"]["organization_name"]
CONTRACT_ID = CONFIG["mets"]["contract_id"]
SIGN_KEY_PATH = CONFIG["sign"]["key_path"]

MUSEUMPLUS_URL = CONFIG["museumplus"]["url"]
LIDO_REPORT_ID = CONFIG["museumplus"]["lido_report_id"]
