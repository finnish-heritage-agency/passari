Installation
============

Installation using virtualenv
-----------------------------

Install Passari
^^^^^^^^^^^^^^^

It is recommended to install Passari and other related software using *virtualenv*, which prevents possible problems with the system's package manager.

To get started, ensure that Python 3.6+ is installed. On CentOS 7, you can usually get started by installing the required tools using `yum`:

.. code-block:: console

    $ yum install python36-libs python36-devel


After this, create a new directory that will contain your virtualenv:

.. code-block:: console

    $ python3.6 -mvenv <venv_dir>
    $ source <venv_dir>/bin/activate
    $ pip install passari

You can disable the *virtualenv* using `deactivate` and activate it with `source <venv_dir>/bin/activate`.

Install dpres-siptools
^^^^^^^^^^^^^^^^^^^^^^

You will also need to install CSC packaging and validation tools. At the time of writing, **you will need to install these into a different virtualenv directory using Python 2.7**. This may not be required in the future once the tools are Python 3 compatible. Read `the official instructions <https://github.com/Digital-Preservation-Finland/dpres-siptools#installation>`_ for details.

Take note of the virtualenv directory you created for *dpres-siptools*; it will be used later when configuring Passari.

Once you have installed *Passari* and *dpres-siptools*, run a command to test that the installation succeeded:

.. code-block:: console

    $ download-object --help
