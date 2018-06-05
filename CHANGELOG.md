CHANGELOG
=========

This document records all notable changes to Watson. This project adheres to
[Semantic Versioning](http://semver.org/).

* Added: the `report` and `log` commands now take a `--json` option to
  format their output in JSON (#167).
* Added: the `status` command now takes `--project`, `--tags`, and `--elapsed`
  options to only output the selected information (#166).
* Added: the `report` and `log` commands' output can now selectively be run
  through a pager (#176).
* Added: the `report` and `log` commands now take an `--all` option to output
  all recorded frames (#185).
* Updated: when renaming a project or tag, the `updated_at` timestamp is
  updated on all affected frames (#181).
* Updated: some enhancements and formatting fixes have been done to the output
  of the `log` and `report` commands (#178, #179, #182).
* Fixed: dependency version restrictions have been added for Watson and its
  tests for continued support of older (2.7 and 3.3) Python versions
  (#175, #180).
* Removed: support for Python 3.3 (#210).

## 1.6.0 (2018-04-23)

* Added: for report and log, allow specifying a timeperiod of "all"
* Added: option for log and report command to (not) output via pager
* Added: --json option to log command
* Added: optional flags to filter status call
* Fixed: change message when frame is removed
* Fixed: cli output when on tags on `stop` and `remove`
* Fixed: Bash completion with latest additions to command options
* Fixed: CLI output spacing if a frame has no tags
* Fixed: frame modification time when renaming projects and tags (#181)
* Fixed: don't print space before tags if there are no tags (#179)
* Fixed: match log daily heading format to elsewhere
* Fixed: set max versions for pytest and arrow for keeping support for Python 2.7 and 3.3

## 1.5.2 (2017-08-02)

* Fixed: Follow up on the `config` command fix (#161)

## 1.5.1 (2017-08-01)

* Fix the `config` command (#158)

## 1.5.0 (2017-07-31)

* Added: the `report` command now supports JSON output (#102)
* Updated: the `sync` command is now compatible with the new crick.io backend
  API (#152)
* Updated: Python 3.6 is now officially supported (#150)
* Fixed: catch error when user wants to edit config but file does not exist yet
  (#154)

## 1.4.0 (2016-11-01)

* Added: Watson now has a `rename` command (#74).
* Added: the `report` and `log` commands now have new command line and
  config file options to (not) include the current frame in the output (#123).
* Added: the `report` and `log` commands now have new command line options to
  set the timespan to the current year, month, week or day (#130 via #124).
* Added: you can now set default tags for selected projects in the
  config file (#113).
* Added: Zsh completion support (#96)
* Added: document installation via homebrew on OS X (#121)
* Updated: when saving the Watson frames, state or config file, the most recent
  previous version of the file is kept as a back up (#120).
* Fixed: bash completion of projects and tags with spaces in them (#122).
* Fixed: if saving the Watson frames, state or config file fails for any
  reason, the original is kept (and not wiped as before) (#120).

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
