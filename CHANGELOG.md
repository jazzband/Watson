CHANGELOG
=========

This document records all notable changes to Watson. This project adheres to
[Semantic Versioning](http://semver.org/).

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
