<!-- 
    This document has been automatically generated.
    It should NOT BE EDITED.
    To update this part of the documentation,
    please type the following from the repository root:
    $ make docs-->

# Commands
## `cancel`

```bash
Usage:  watson cancel [OPTIONS]
```

Cancel the last call to the start command. The time will
not be recorded.

### Options

Flag | Help
-----|-----
`--help` | Show this message and exit.

## `config`

```bash
Usage:  watson config [OPTIONS] SECTION.OPTION [VALUE]
```

Get and set configuration options.

If value is not provided, the content of the key is displayed. Else,
the given value is set.

You can edit the config file with an editor with the `--edit` option.

Example:


    $ watson config backend.token 7e329263e329
    $ watson config backend.token
    7e329263e329

### Options

Flag | Help
-----|-----
`-e, --edit` | Edit the configuration file with an editor.
`--help` | Show this message and exit.

## `edit`

```bash
Usage:  watson edit [OPTIONS] [ID]
```

Edit a frame.

You can specify the frame to edit by its position or by its frame id.
For example, to edit the second-to-last frame, pass `-2` as the frame
index. You can get the id of a frame with the `watson log` command.

If no id or index is given, the frame defaults to the current frame or the
last recorded frame, if no project is currently running.

The `$EDITOR` environment variable is used to detect your editor.

### Options

Flag | Help
-----|-----
`--help` | Show this message and exit.

## `frames`

```bash
Usage:  watson frames [OPTIONS]
```

Display the list of all frame IDs.

Example:


    $ watson frames
    f1c4815
    9d1a989
    8801ec3
    [...]

### Options

Flag | Help
-----|-----
`--help` | Show this message and exit.

## `help`

```bash
Usage:  watson help [OPTIONS] [COMMAND]
```

Display help information

### Options

Flag | Help
-----|-----
`--help` | Show this message and exit.

## `log`

```bash
Usage:  watson log [OPTIONS]
```

Display each recorded session during the given timespan.

By default, the sessions from the last 7 days are printed. This timespan
can be controlled with the `--from` and `--to` arguments. The dates
must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

You can also use special shortcut options for easier timespan control:
`--day` sets the log timespan to the current day (beginning at 00:00h)
and `--year`, `--month` and `--week` to the current year, month or week
respectively.

You can limit the log to a project or a tag using the `--project` and
`--tag` options. They can be specified several times each to add multiple
projects or tags to the log.

Example:


    $ watson log --project voyager2 --project apollo11
    Thursday 08 May 2015 (56m 33s)
            f35bb24  09:26 to 10:22      56m 33s  apollo11  [reactor, brakes, steering, wheels, module]
    
    Wednesday 07 May 2015 (27m 29s)
            9a1325d  09:48 to 10:15      27m 29s  voyager2  [sensors, generators, probe]
    
    Tuesday 06 May 2015 (1h 47m 22s)
            530768b  12:40 to 14:16   1h 35m 45s  apollo11  [wheels]
            84164f0  14:23 to 14:35      11m 37s  apollo11  [brakes, steering]
    
    Monday 05 May 2015 (8h 18m 26s)
            26a2817  09:05 to 10:03      57m 12s  voyager2  [probe, generators]
            5590aca  10:51 to 14:47   3h 55m 40s  apollo11
            c32c74e  15:12 to 18:38   3h 25m 34s  voyager2  [probe, generators, sensors, antenna]
    
    $ watson log --from 2014-04-16 --to 2014-04-17
    Thursday 17 April 2014 (4h 19m 13s)
            a96fcde  09:15 to 09:43      28m 11s    hubble  [lens, camera, transmission]
            5e91316  10:19 to 12:59   2h 39m 15s    hubble  [camera, transmission]
            761dd51  14:42 to 15:54   1h 11m 47s  voyager1  [antenna]
    
    Wednesday 16 April 2014 (5h 19m 18s)
            02cb269  09:53 to 12:43   2h 50m 07s  apollo11  [wheels]
            1070ddb  13:48 to 16:17   2h 29m 11s  voyager1  [antenna, sensors]

### Options

Flag | Help
-----|-----
`-c, --current / -C, --no-current` | (Don't) include currently running frame in output.
`-f, --from DATE` | The date from when the log should start. Defaults to seven days ago.
`-t, --to DATE` | The date at which the log should stop (inclusive). Defaults to tomorrow.
`-y, --year` | Reports activity for the current year.
`-m, --month` | Reports activity for the current month.
`-w, --week` | Reports activity for the current week.
`-d, --day` | Reports activity for the current day.
`-p, --project TEXT` | Logs activity only for the given project. You can add other projects by using this option several times.
`-T, --tag TEXT` | Logs activity only for frames containing the given tag. You can add several tags by using this option multiple times
`--help` | Show this message and exit.

## `merge`

```bash
Usage:  watson merge [OPTIONS] FRAMES_WITH_CONFLICT
```

Perform a merge of the existing frames with a conflicting frames file.

When storing the frames on a file hosting service, there is the
possibility that the frame file goes out-of-sync due to one or
more of the connected clients going offline. This can cause the
frames to diverge.

If the `--force` command is specified, the merge operation
will automatically be performed.

The only argument is a path to the the conflicting `frames` file.

Merge will output statistics about the merge operation.

Example:


    $ watson merge frames-with-conflicts
    120 frames will be left unchanged
    12  frames will be merged
    3   frame conflicts need to be resolved
    
To perform a merge operation, the user will be prompted to
select the frame they would like to keep.

Example:


    $ watson merge frames-with-conflicts --force
    120 frames will be left unchanged
    12  frames will be merged
    3   frame conflicts need to be resolved
    Will resolve conflicts:
    frame 8804872:
    < {
    <     "project": "tailordev",
    <     "start": "2015-07-28 09:33:33",
    <     "stop": "2015-07-28 10:39:36",
    <     "tags": [
    <         "intern",
    <         "daily-meeting"
    <     ]
    < }
    ---
    > {
    >     "project": "tailordev",
    >     "start": "2015-07-28 09:33:33",
    >     "stop": "**2015-07-28 11:39:36**",
    >     "tags": [
    >         "intern",
    >         "daily-meeting"
    >     ]
    > }
    Select the frame you want to keep: left or right? (L/r)

### Options

Flag | Help
-----|-----
`-f, --force` | If specified, then the merge will automatically be performed.
`--help` | Show this message and exit.

## `projects`

```bash
Usage:  watson projects [OPTIONS]
```

Display the list of all the existing projects.

Example:


    $ watson projects
    apollo11
    hubble
    voyager1
    voyager2

### Options

Flag | Help
-----|-----
`--help` | Show this message and exit.

## `remove`

```bash
Usage:  watson remove [OPTIONS] ID
```

Remove a frame. You can specify the frame either by id or by position
(ex: `-1` for the last frame).

### Options

Flag | Help
-----|-----
`-f, --force` | Don't ask for confirmation.
`--help` | Show this message and exit.

## `rename`

```bash
Usage:  watson rename [OPTIONS] TYPE OLD_NAME NEW_NAME
```

Rename a project or tag.

Example:


    $ watson rename project read-python-intro learn-python
    Renamed project "read-python-intro" to "learn-python"
    $ watson rename tag company-meeting meeting
    Renamed tag "company-meeting" to "meeting"

### Options

Flag | Help
-----|-----
`--help` | Show this message and exit.

## `report`

```bash
Usage:  watson report [OPTIONS]
```

Display a report of the time spent on each project.

If a project is given, the time spent on this project is printed.
Else, print the total for each root project.

By default, the time spent the last 7 days is printed. This timespan
can be controlled with the `--from` and `--to` arguments. The dates
must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

You can also use special shortcut options for easier timespan control:
`--day` sets the report timespan to the current day (beginning at 00:00h)
and `--year`, `--month` and `--week` to the current year, month or week
respectively.

You can limit the report to a project or a tag using the `--project` and
`--tag` options. They can be specified several times each to add multiple
projects or tags to the report.

Example:


    $ watson report
    Mon 05 May 2014 -> Mon 12 May 2014
    
    apollo11 - 13h 22m 20s
            [brakes    7h 53m 18s]
            [module    7h 41m 41s]
            [reactor   8h 35m 50s]
            [steering 10h 33m 37s]
            [wheels   10h 11m 35s]
    
    hubble - 8h 54m 46s
            [camera        8h 38m 17s]
            [lens          5h 56m 22s]
            [transmission  6h 27m 07s]
    
    voyager1 - 11h 45m 13s
            [antenna     5h 53m 57s]
            [generators  9h 04m 58s]
            [probe      10h 14m 29s]
            [sensors    10h 30m 26s]
    
    voyager2 - 16h 16m 09s
            [antenna     7h 05m 50s]
            [generators 12h 20m 29s]
            [probe      12h 20m 29s]
            [sensors    11h 23m 17s]
    
    Total: 43h 42m 20s
    
    $ watson report --from 2014-04-01 --to 2014-04-30 --project apollo11
    Tue 01 April 2014 -> Wed 30 April 2014
    
    apollo11 - 13h 22m 20s
            [brakes    7h 53m 18s]
            [module    7h 41m 41s]
            [reactor   8h 35m 50s]
            [steering 10h 33m 37s]
            [wheels   10h 11m 35s]

### Options

Flag | Help
-----|-----
`-c, --current / -C, --no-current` | (Don't) include currently running frame in report.
`-f, --from DATE` | The date from when the report should start. Defaults to seven days ago.
`-t, --to DATE` | The date at which the report should stop (inclusive). Defaults to tomorrow.
`-y, --year` | Reports activity for the current year.
`-m, --month` | Reports activity for the current month.
`-w, --week` | Reports activity for the current week.
`-d, --day` | Reports activity for the current day.
`-p, --project TEXT` | Reports activity only for the given project. You can add other projects by using this option several times.
`-T, --tag TEXT` | Reports activity only for frames containing the given tag. You can add several tags by using this option multiple times
`--help` | Show this message and exit.

## `restart`

```bash
Usage:  watson restart [OPTIONS] [FRAME]
```

Restart monitoring time for a previously stopped project.

By default, the project from the last frame, which was recorded, is
restarted, using the same tags as recorded in that frame. You can specify
the frame to use with an integer frame index argument or a frame ID. For
example, to restart the second-to-last frame, pass `-2` as the frame index.

Normally, if a project is currently started, watson will print an error and
do nothing. If you set the configuration option `options.stop_on_restart`
to a true value (`1`, `on`, `true` or `yes`), the current project, if any,
will be stopped before the new frame is started. You can pass the option
`-s` or `--stop` resp. `-S` or `--no-stop` to override the default or
configured behaviour.

If no previous frame exists or an invalid frame index or ID was given,
an error is printed and no further action taken.

Example:


    $ watson start apollo11 +module +brakes
    Starting project apollo11 [module, brakes] at 16:34
    $ watson stop
    Stopping project apollo11, started a minute ago. (id: e7ccd52)
    $ watson restart
    Starting project apollo11 [module, brakes] at 16:36

### Options

Flag | Help
-----|-----
`-s, --stop / -S, --no-stop` | (Don't) Stop an already running project.
`--help` | Show this message and exit.

## `start`

```bash
Usage:  watson start [OPTIONS] [ARGS]...
```

Start monitoring time for the given project.
You can add tags indicating more specifically what you are working on with
`+tag`.

If there is already a running project and the configuration option
`options.stop_on_start` is set to a true value (`1`, `on`, `true` or
`yes`), it is stopped before the new project is started.

Example:


    $ watson start apollo11 +module +brakes
    Starting project apollo11 [module, brakes] at 16:34

### Options

Flag | Help
-----|-----
`--help` | Show this message and exit.

## `status`

```bash
Usage:  watson status [OPTIONS]
```

Display when the current project was started and the time spent since.

You can configure how the date and time of when the project was started are
displayed by setting `options.date_format` and `options.time_format` in the
configuration. The syntax of these formatting strings and the supported
placeholders are the same as for the `strftime` method of Python's
`datetime.datetime` class.

Example:


    $ watson status
    Project apollo11 [brakes] started seconds ago (2014-05-19 14:32:41+0100)
    $ watson config options.date_format %d.%m.%Y
    $ watson config options.time_format "at %I:%M %p"
    $ watson status
    Project apollo11 [brakes] started a minute ago (19.05.2014 at 02:32 PM)

### Options

Flag | Help
-----|-----
`--help` | Show this message and exit.

## `stop`

```bash
Usage:  watson stop [OPTIONS]
```

Stop monitoring time for the current project.

You can optionally pass a log message to be saved with the frame via
the ``-m/--message`` option.

Example:


    $ watson stop -m "Done some thinking"
    Stopping project apollo11, started a minute ago. (id: e7ccd52)
    Log message: Done some thinking

### Options

Flag | Help
-----|-----
`-m, --message TEXT` | Save given log message with the project frame.
`--help` | Show this message and exit.

## `sync`

```bash
Usage:  watson sync [OPTIONS]
```

Get the frames from the server and push the new ones.

The URL of the server and the User Token must be defined via the
`watson config` command.

Example:


    $ watson config backend.url http://localhost:4242
    $ watson config backend.token 7e329263e329
    $ watson sync
    Received 42 frames from the server
    Pushed 23 frames to the server

### Options

Flag | Help
-----|-----
`--help` | Show this message and exit.

## `tags`

```bash
Usage:  watson tags [OPTIONS]
```

Display the list of all the tags.

Example:


    $ watson tags
    antenna
    brakes
    camera
    generators
    lens
    module
    probe
    reactor
    sensors
    steering
    transmission
    wheels

### Options

Flag | Help
-----|-----
`--help` | Show this message and exit.

