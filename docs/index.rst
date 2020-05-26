.. Passari documentation master file, created by
   sphinx-quickstart on Mon May 25 16:30:06 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Passari's documentation!
===================================

**Passari** is a set of command-line tools to download objects from MuseumPlus, package them into Submission Information Packages and upload them into the Finnish National Digital Preservation Service.

Passari has only been tested with CentOS 7 -- other environments might require additional effort, including the installation of validation and packaging tools provided by CSC that are required by this software.

The command-line tools in this repository are designed to work standalone, and can be used manually when submitting a small number of packages, or integrated as part of another system.

.. note::

   For an automated workflow that uses Passari, see *passari-workflow*.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   configuration
   usage
   development
