# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [1.1] - 2020-08-04
### Added
 - Raise PreservationError for MPO/JPEG files.
 - Raise PreservationError for non-ASCII filenames due to the DPRES service not supporting such filenames for now.
 - Raise PreservationError for unsupported JPEG versions.

### Fixed
 - Reject attachments with the filename 'Multimedia.xml' that would cause the file to be overwritten.
 - Shutdown running async tasks properly before raising exceptions.
 - Check HTTP status when downloading attachments.

## 1.0 - 2020-06-17
### Added
 - First release.

[1.1]: https://github.com/finnish-heritage-agency/passari/compare/1.0...1.1
