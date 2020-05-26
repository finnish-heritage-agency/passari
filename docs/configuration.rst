Configuration
=============

Once you have installed *Passari*, run a command such as the following:

.. code-block:: console

    $ download-object --help

This should print a help message, as well as create a configuration file in your user's configuration directory if it doesn't exist already. You should find it in `~/.config/passari/config.toml`.

The contents of the file should look like this:

.. code-block::

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
   organization_name='National Board of Antiquities'
   # Contract ID used for DPRES REST API and in PREMIS events
   contract_id='12345678-f00d-d00f-a4b7-010a184befdd'

   [sign]
   # Path to the key used to sign the METS
   key_path='/home/user/passari-venv/lib64/python3.7/site-packages/passari/data/test_rsa_keys.crt'

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


MuseumPlus account
------------------

*Passari* will require a MuseumPlus account with sufficient privileges to download objects and write DPRES log entries (if enabled).

.. note::

   Passari will not filter the preserved objects by itself, and you will need to limit access to objects you don't want to be preserved on the MuseumPlus side.

   This is important if multiple *Passari* services are being used for a single *MuseumPlus* instance; otherwise the same object may be preserved multiple times by different organizations.

Parameters
----------

- ``mets/organization_name`` - name of the organization that is submitting packages to the preservation service
- ``mets/contract_id`` - contract ID used in PREMIS events

- ``sign/key_path`` - path to `.crt` key file that will be used to sign the packages

- ``ssh/host`` - SSH host of the DPRES service
- ``ssh/port`` - SSH port of the DPRES service
- ``ssh/username`` - SSH username used to login to the SSH server
- ``ssh/private_key`` - private key used to login to the SSH server
- ``ssh/home_path`` - home path of the SFTP server. This can be `/home/<username>` or just `/` depending on how the SFTP server is configured.
- ``museumplus/url`` - URL to the MuseumPlus API endpoint that ends with `/ria-ws/application`
- ``museumplus/lido_report_id`` - Template ID used for generating the LIDO XML report
- ``museumplus/object_preservation_field_name`` - Field name for DPRES log entries
- ``museumplus/object_preservation_field_type`` - Field type for DPRES log entries. This should be just `dataField`.
- ``museumplus/add_log_entries`` - whether to add log entries to the field defined in `museumplus/object_preservation_field_name`
- ``museumplus/username`` - MuseumPlus username
- ``museumplus/password`` - MuseumPlus password
- ``dpres/use_virtualenv`` - whether to use a different virtualenv for running `dpres-siptools` commands. This is required if the tools are not installed in the same virtualenv. At the time of writing, this is due to *dpres-siptools* having support for Python 2.7 while *Passari* is written for Python 3.6.
- ``dpres/virtualenv_path`` - path to the virtualenv containing the `dpres-siptools` installation, if enabled.
