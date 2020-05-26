Development
===========

Known errors
------------

*Passari* tries to detect some known error cases when creating SIPs, and raises a ``passari.exceptions.PreservationError`` instead when a known error case is detected. These are used in *passari-workflow* to handle the Objects automatically: for example, if an attachment is a TIFF image but it has multiple pages, the related Object will be frozen and added into a list of Objects that have been frozen for the same reason.

This error detection is handled by a list of *error detectors*, classes that check the exception and raise a ``PreservationError`` if they recognize the error case. The first class that raises a ``PreservationError`` "wins", so any exception that occurs during SIP creation can only result in one ``PreservationError``.

The error detectors can be found in ``src/passari/dpres/errors.py``. At the moment, only ``subprocess.CalledProcessError`` exceptions raised by ``import-object`` will be checked for known errors.

PREMIS events
-------------

*Passari* adds PREMIS events by inspecting the ``passari.dpres.MuseumObjectPackage`` instance for any data that means some event took place. For example, a ``creation`` PREMIS event will be added if the MuseumObject has a valid creation date in the MuseumPlus service.

Events are created by *event creators* which can be found in ``src/passari/dpres/events.py``.
