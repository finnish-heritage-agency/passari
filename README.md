Passari
=======

Tools for downloading objects from Museum Plus service, packaging them into Submission Information Packages and uploading them into the Finnish National Digital Preservation service.

The tools in this repository are implemented as self-contained scripts, which allows easier testing and debugging. These tools are integrated into a workflow in the `passari-workflow` repository, which allows the preservation process to be automated for larger datasets.

The tools have been only tested with CentOS 7.

Installation
------------

The tools are written in Python 3. To get started, install Python 3 and create a virtualenv:

```
sudo dnf install python3 python3-virtualenv
python3 -mvenv venv
source venv/bin/activate
pip install .
```

You can now use the different tools (eg. `download-object`).

Configuration
-------------

Upon startup, a configuration file will be created in the default location; in Linux
this is usually `~/.config/passari/config.toml`. Fill the configuration file
with required options (eg. MuseumPlus credentials).
