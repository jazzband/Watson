# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2020-03-19

### Added

- The `log` command output can now be filtered to exclude projects and tags via
  `--ignore-project` and `--ignore-tag` (#395)
- Python 3.8 support (#402)
- Python 3.9 support (#402)
- Support for the TZ environment variable to specify the local time zone (#391)

### Changed

- Upgrade to major arrow release 1.0.0 (#407)

### Fixed

- Zsh completion (#379)

### Removed

- Python 2.7 support (#305).
- Python 3.5 support (#407).

## [1.10.0] - 2020-07-03

### Added

- Log output order can now be controlled via the `--reverse/--no-reverse` flag
  and the `reverse_log` configuration option (#369)
- Add `--at` flag to the `start` and `restart` commands (#364).
- Add `--color` and `--no-color` flags to force output to be colored or not
  respectively (#350).

### Changed

- Require latest Arrow version 0.15.6 to support ISO week dates (#380)

### Fixed

- Make after-edit-check ensure that edited time stamps are not in the future
  (#381)

## [1.9.0] - 2020-05-27

### Added

- Improve Arrow 0.15.0 support after changes in `arrow.get()` behavior (#296)
- Watson now suggests correct command if users make small typo (#318)

### Changed

- Always show total time at bottom of report (#356)
- Use the default system newline character for CSV output (#366).

### Fixed

- Stylize prompt to create new project or tag (#310).
- Aggregate calculates wrong time if used with `--current` (#293)
- The `start` command now correctly checks if project is empty (#322)
- Aggregate ignores frames that crosses aggregate boundary (#248)
- The `report` and `aggregate` commands with `--json` option now correctly
  encode Arrow objects (#329)

## [1.8.0] - 2019-08-26

### Added

- Add CSV output format support for `report`, `log` and `aggregate` commands
  using the `--csv/-s` command line option flag (#281).
- Add `start --confirm-new-project` and `start --confirm-new-tag` options and
  corresponding options to configuration (#275).

### Fixed

- Update zsh shell completion (#264).
- Fix fatal AttributeError using Arrow 0.14.5 (#300)

### Removed

- Python 3.4 support (#286).

## [1.7.0] - 2019-03-25

### Added

- New `add` command (#202)
- Add lunar start time options to the `report` and `log` commands (#215)
- Aggregate reports by day (#231)
- Fish shell completion (#239)
- Add support for first day of the week configuration in reports and logs (#240)
- Python 3.7 support (#241)
- Add `start --no-gap` and `stop --at` options (#254)
- Add `--confirm-new-project` and `--confirm-new-tag` options to `start`, `add` and `edit` commands (#275)

### Changed

- The `edit` command now checks data consistency (#203)
- Current state saving is now improve when using Watson as a library (#214)
- Prevent calling `get_start_time_for_period` multiple times (#219)

### Fixed

- Improved support for UTF-8 with Python 2 (#211)
- Zsh completion for tags and projects with spaces in their names (#227)
- Typos in commands output (#230, #235)
- Project URL of the project in PyPI (#260)

### Removed

- Python 3.3 support (#210).

## [1.6.0] - 2018-04-23

### Added

- For `report` and `log`, allow specifying a timeperiod of "all"
- Option for log and report command to (not) output via pager
- `--json` option to log command
- Optional flags to filter status call

### Fixed

- Change message when frame is removed
- CLI output when on tags on `stop` and `remove`
- Bash completion with latest additions to command options
- CLI output spacing if a frame has no tags
- Frame modification time when renaming projects and tags (#181)
- Don't print space before tags if there are no tags (#179)
- Match log daily heading format to elsewhere
- Set max versions for pytest and arrow for keeping support for Python 2.7 and
  3.3

## [1.5.2] - 2017-08-02

### Fixed

- Follow up on the `config` command fix (#161)

## [1.5.1] - 2017-08-01

### Fixed

- Fix the `config` command (#158)

## [1.5.0] - 2017-07-31

### Added

- The `report` command now supports JSON output (#102)

### Changed

- The `sync` command is now compatible with the new crick.io backend API (#152)
- Python 3.6 is now officially supported (#150)

### Fixed

- Catch error when user wants to edit config but file does not exist yet (#154)

## [1.4.0] - 2016-11-01

### Added

- Watson now has a `rename` command (#74).
- The `report` and `log` commands now have new command line and config file
  options to (not) include the current frame in the output (#123).
- The `report` and `log` commands now have new command line options to set the
  timespan to the current year, month, week or day (#130 via #124).
- You can now set default tags for selected projects in the config file (#113).
- Zsh completion support (#96)
- Document installation via homebrew on OS X (#121)

### Changed

- When saving the Watson frames, state or config file, the most recent previous
  version of the file is kept as a back up (#120).

### Fixed

- Bash completion of projects and tags with spaces in them (#122).
- If saving the Watson frames, state or config file fails for any reason, the
  original is kept (and not wiped as before) (#120).

## [1.3.2] - 2016-03-01

### Added

- Document installation for Arch Linux
- Improve frame selection by position

### Fixed

- Improve error handling
- Remove unnecessary dependencies for a stand alone installation
- Specify correct source directory for flake8 and pytest (tox test suite)

## [1.3.1] - 2016-02-11

### Fixed

- Packaging issue with PyPI

## [1.3.0] - 2016-02-11

### Added

- A complete browsable documentation
- Watson's brand new logo!
- Support for Watson's directory override via the WATSON_DIR environment variable

## [1.2.0] - 2016-01-22

### Added

- Watson now has a `restart` command
- Watson now has a `merge` command
- Watson can now stop running project when starting a new one (optional)
- There is a wrapper for `RawConfigParser` to make option access more convenient

### Updated

- The `edit` command now defaults to the running frame if any (else defaults to
  the last one)
- The `log` command now has a daily total time summary

### Fixed

- Unicode issues with cjk characters
- Edition summary is now converted to local time

## [1.1.0] - 2015-10-21

### Added

- Configurable date and time to output of `status` command (#33)
- Support for Bash-completion (#1)
- New `frames` command that displays all frame IDs

### Fixed

- Set id if not provided (#30)

## [1.0.2] - 2015-10-09

### Added

- Add documentation to remove all the frames

### Changed

- Improve installation instructions

### Fixed

- The last frame could not be deleted

## [1.0.1] - 2015-09-17

### Fixed

- Packaging erissueror with PyPI

## [1.0.0] - 2015-09-17

First stable public release 🎉

[unreleased]: https://github.com/tailordev/watson/compare/2.0.0...HEAD
[2.0.0]: https://github.com/tailordev/watson/compare/1.10.0...2.0.0
[1.10.0]: https://github.com/tailordev/watson/compare/1.9.0...1.10.0
[1.9.0]: https://github.com/tailordev/watson/compare/1.8.0...1.9.0
[1.8.0]: https://github.com/tailordev/watson/compare/1.7.0...1.8.0
[1.7.0]: https://github.com/tailordev/watson/compare/1.6.0...1.7.0
[1.6.0]: https://github.com/tailordev/watson/compare/1.5.2...1.6.0
[1.5.2]: https://github.com/tailordev/watson/compare/1.5.1...1.5.2
[1.5.1]: https://github.com/tailordev/watson/compare/1.5.0...1.5.1
[1.5.0]: https://github.com/tailordev/watson/compare/1.4.0...1.5.0
[1.4.0]: https://github.com/tailordev/watson/compare/1.3.2...1.4.0
[1.3.2]: https://github.com/tailordev/watson/compare/1.3.1...1.3.2
[1.3.1]: https://github.com/tailordev/watson/compare/1.3.0...1.3.1
[1.3.0]: https://github.com/tailordev/watson/compare/1.2.0...1.3.0
[1.2.0]: https://github.com/tailordev/watson/compare/1.1.0...1.2.0
[1.1.0]: https://github.com/tailordev/watson/compare/1.0.2...1.1.0
[1.0.2]: https://github.com/tailordev/watson/compare/1.0.1...1.0.2
[1.0.1]: https://github.com/tailordev/watson/compare/1.0.0...1.0.1
[1.0.0]: https://github.com/tailordev/watson/releases/tag/1.0.0
