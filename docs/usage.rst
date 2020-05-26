Usage
=====

*Passari* consists of stand-alone command-line tools for the different steps of the preservation workflow:

- ``download-object`` - download Object from MuseumPlus
- ``create-sip`` - package the downloaded Object into a Submission Information Package (SIP)
- ``submit-sip`` - upload the SIP into the DPRES service
- ``confirm-sip`` - confirm that the SIP was either accepted or rejected in the DPRES service, and download the reports

Example: preserving a single Object
-----------------------------------

In this example, we have a single Object with the ID `42` that we want to submit into the DPRES service.

Start by creating two directories that will hold the objects under processing and archived reports from confirmed SIPs respectively:

.. code-block:: console

    $ mkdir ~/MuseumObjects
    $ mkdir ~/MuseumArchive

.. note::

   It is recommended to place the ``MuseumObjects`` directory into a performant file system, while ``MuseumArchive`` directory can be placed into a file system that is designed for only occasional reads.

Start by downloading the Object

.. code-block:: console

    $ download-object --package-dir ~/MuseumObjects 42

This should download the Object into a new directory `~/MuseumObjects/42`. If this command succeeded, package the SIP:

.. code-block:: console

    $ create-sip --package-dir ~/MuseumObjects --create-date "2020-01-01T12:15:20+00:00" 42

.. note::

   You may need to upload the same Object multiple times. This can happen if your first attempt at submitting the SIP is rejected due to some issue.

   In this case, you can use the ``--sip-id`` parameter to give unique identifiers to the different SIPs that are created from the same Object. The value of SIP ID can be arbitrary: for example, you can use the time of packaging as the SIP ID.

   If provided, you **will** need to use the ``--sip-id`` with the subsequent ``submit-sip`` and ``confirm-sip`` commands as well.

.. note::

   ``--create-date`` parameter is optional, but it must be used if you want to update the SIP at a later date. When updating the SIP you'll need to provide the same creation date you used before.

If the Object was packaged successfully, you can submit it using ``submit-sip``:

.. code-block:: console

   $ submit-sip --package-dir ~/MuseumObjects 42

At this point, the DPRES service will eventually process the package and either accept it or reject it. **You will have to check this manually; Passari does not check the SIP's status for you.**

.. note::

   You can check the SIP's status by either looking for a new directory in the `accepted` or `rejected` directories using a SFTP client, or by querying the DPRES REST API.

   For details, see `the interface documentation <http://digitalpreservation.fi/en/specifications>`_.

Finally, after the Object is either accepted or rejected in the DPRES service, you can run the final command to download the reports for the SIP:

.. code-block:: console

   $ confirm-sip --package-dir ~/MuseumObjects --archive-dir ~/MuseumArchive --status accepted 42

After this, you should have now successfully submitted an Object to the DPRES service!

Example: updating a submitted Object
------------------------------------

After a certain amount of time has passed, the underlying Object may change (eg. new attachments are uploaded), which may necessiate updating the SIP in digital preservation.

Updating involves calling the ``create-sip`` with different parameters, but otherwise the workflow is the same (``download-object``, ``create-sip``, ``submit-sip`` and ``confirm-sip``).

Note the new ``--modify-date`` and ``--update`` parameters when calling ``create-sip``. ``--create-date`` must have the same value as before:

.. code-block:: console

    $ create-sip --package-dir ~/MuseumObjects --create-date "2020-01-01T12:15:20+00:00" --modify-date "2020-02-02T12:15:20+00:00" --update 42
