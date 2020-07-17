This directory contains test files that are used to construct mock MuseumPlus responses.

There are currently test files for the following fake objects:

* Object 1234567
  * contains attachments 1234567001 (kuva1.JPG) and 1234567002 (kuva2.JPG), which are normal JPEG files
* Object 1234568
  * has no attachments
* Object 1234569
  * has attachment 1234569001 (test.zip), which will be extracted during SIP creation process, as ZIP archives are not allowed to be preserved
* Object 1234570
  * has unsupported attachment 1234570001 (test.wad), which will raise a PreservationError when SIP creation is attempted
* Object 1234571
  * has no creation date
* Object 1234572
  * was migrated from Musketti and has one attachment
* Object 1234573
  * has empty attachment 1234573001
* Object 1234574
  * was migrated from Musketti and has one attachment that was migrated from Musketti as well
* Object 1234575
  * has attachments 1234575001 with no creation date
* Object 1234576
  * has attachment 1234576001 (test.JPG) which will raise a PreservationError (for now) due to insufficient JPEG version detection support
* Object 1234577
  * has attachment 1234577001 (test.TIF) which will raise a PreservationError due to being detected as invalid by JHOVE
* Object 1234578
  * has barebones Object document with only systemField entries. Trying to download this will trigger an exception.
* Object 1234579
  * is linked to collection activities 765432001 and 765432002
* Object 1234580
  * has attachment 1234580001 (test.TIF) which will raise a PreservationError due to being a multi-page TIFF
* Object 1234581
  * has attachment 1234581001 (test.JPG) which will raise a PreservationError due to being a MPO/JPEG image file
* Object 1234582
  * has attachment 1234582001 (kärpänen.JPG) which will raise a PreservationError due to the non-ASCII filename, which is not supported by the DPRES service at the time of writing
