from contextlib import closing, contextmanager

import paramiko

from passari.config import CONFIG


@contextmanager
def connect_dpres_sftp():
    """
    Context manager to connect to the DPRES service's SFTP server and return
    a connection instance
    """
    host = CONFIG["ssh"]["host"]
    port = int(CONFIG["ssh"]["port"])

    with closing(paramiko.Transport((host, port))) as transport:
        private_key = paramiko.RSAKey.from_private_key_file(
            CONFIG["ssh"]["private_key"]
        )
        transport.connect(
            username=CONFIG["ssh"]["username"],
            pkey=private_key
        )

        yield paramiko.SFTPClient.from_transport(transport)
