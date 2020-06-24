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

MuseumPlus gotchas
------------------

The MuseumPlus API can behave unexpectedly in some situations. Passari uses workarounds where applicable, but these "gotchas" can also be helpful for other developers using the API:

- The API may return the HTTP error **503 - Service Unavailable**. This can happen due to insufficient user permissions, **not** due to server problems.
- The API can return the HTTP error **403 - Forbidden** if the credentials (username and password) are incorrect **or** if the current session has expired. Due to this ambiguity, Passari renews session preemptively before expiration to ensure that this issue does not occur.
- Using the **HTTP Basic Auth** authentication method causes a login event on each request -- prefer the **User session service** instead. Passari uses the user session service.
- The connection may hang indefinitely at random -- ensure that your HTTP requests have a set timeout.
- The API may silently truncate returned XML documents by removing all fields with types other than ``systemField`` from the response due to insufficient user permissions. Passari checks for this by ensuring the XML documents contain module fields with types other than ``systemField`` and raising an exception if this is not the case.
- The ISO 8601 timestamps in the XML documents use the UTC time zone. This *might* depend on the installation, so check this beforehand if you're not sure.
- The API doesn't provide a way to check the attachment file size. When downloading attachments, ensure that plenty of free disk space is available or try storing less attachments simultaneously to avoid sudden "disk full" issues.
