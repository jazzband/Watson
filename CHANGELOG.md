CHANGELOG
=========

This document records all notable changes to Watson. This project adheres to
[Semantic Versioning](http://semver.org/).

## Development

* Added: Watson now has a `rename` command.
* Added: the `report` and `log` commands now have new command line and
  config file options to (not) include the current frame in the output.
* Added: the `report` and `log` commands now have new options to set the
  timespan to the current year, month, week or day.
* Added: Zsh completion support
* Added: document installation via homebrew on OS X
* Updated: when saving the Watson frames, state or config file, the most recent
  previous version of the file is kept as a back up.
* Fixed: bash completion of projects and tags with spaces in them
* Fixed: if saving the Watson frames, state or config file fails for any
  reason, the original is kept (and not wiped as before).

## 1.3.2 (2016-03-01)

* Added: document installation for Arch Linux
* Added: improve frame selection by position
* Fixed: improve error handling
* Fixed: remove unnecessary dependencies for a stand alone installation
* Fixed: specify correct source directory for flake8 and pytest (tox test
  suite)

## 1.3.1 (2016-02-11)

* Fix packaging error with PyPI

## 1.3.0 (2016-02-11)

* Add a complete browsable documentation
* Add Watson's brand new logo!
* Add support for Watson's directory override via the WATSON_DIR environment variable

## 1.2.0 (2016-01-22)

* Added: Watson now has a `restart` command
* Added: Watson now has a `merge` command
* Added: Watson can now stop running project when starting a new one (optional)
* Added: there is a wrapper for `RawConfigParser` to make option access more convenient
* Updated: the `edit` command now defaults to the running frame if any (else defaults to the last one)
* Updated: the `log` command now has a daily total time summary
* Fixed: unicode issues with cjk characters
* Fixed: edition summary is now converted to local time

## 1.1.0 (2015-10-21)

* Added: configurable date and time to output of `status` command (#33)
* Added: support for Bash-completion (#1)
* Added: new `frames` command that displays all frame IDs
* Fixed: set id if not provided (#30)

## 1.0.2 (2015-10-09)

* Fix a bug where the last frame could not be deleted
* Improve installation instructions
* Add an explanation to remove all the frames

## 1.0.1 (2015-09-17)

* Fix packaging error with PyPI

## 1.0.0 (2015-09-17)

* First stable version
