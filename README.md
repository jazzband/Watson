Watson [![Build Status](https://travis-ci.org/TailorDev/Watson.svg)](https://travis-ci.org/TailorDev/Watson)
======

Watson is here to help you monitoring your time. You want to know how much time
you are spending on your projects? You want to generate a nice report for your
client? Watson is here for you.

Tell Watson when you start working on a task with the `start` command. Then,
when you are done with this task, stop the timer with the `stop` command. This will create what we call a **frame**. That's pretty much everything you need to know to start using Watson.

Each frame consists of the name of a project and some tags. Your tags can be shared across projects and can be used to generate detailed reports.

Watson stores everything on your computer, but you can go wild and use
[artich.io](https://artich.io/?pk_campaign=GitHubWatson) to store your sessions remotely and share it with your colleagues.

<p align="center">
  <img src="screenshot.png" alt="Watson"/>
</p>

## Install

Watson is available on any platform supported by Python (Windows, Mac, Linux,
*BSD…). The easiest way to install it is to use [pip](https://pip.pypa.io/en/stable/installing/):

```bash
$ pip install td-watson
```

You might need to run this command as root in order to install Watson globally.

Alternatively, you can choose to install Watson for your user only by running:

```bash
$ pip install --user td-watson
```

If after this the `watson` command is not available, you need to add `~/.local/bin/` to your PATH. If your terminal is Bash, you can do this by running:

```bash
$ echo 'export PATH="$HOME/.local/bin:$PATH"' >> .bashrc  # Add ~/.local/bin/ to your .bashrc PATH
```

and restarting your terminal session.

### Development version

The latest development version can be installed using the following commands:

```bash
$ git clone https://github.com/TailorDev/Watson.git
$ cd Watson/
$ python setup.py install
```

### Command line completion

If you use a Bash-compatible shell, you can install the `watson.completion`
file from the source distribution as `/etc/bash.completion.d/watson` - or
wherever your distribution keeps the Bash completion configuration files.
After you restart your shell, you can then just type `watson` on your command
line and then hit TAB to see all available commands. Depending on your input,
it completes watson commands, command options, projects, tags and frame IDs.

## Commands

Here is the listing of all the commands available with Watson. You can also
find this help with `watson help`.

### start

Start monitoring the time for the given project. You can add tags
indicating more specifically what you are working on with '+tag'.

```
Example :
$ watson start apollo11 +module +brakes
Starting apollo11 [module, brakes] at 16:34
```

### stop

Stop monitoring time for the current project

```
$ watson stop
Stopping project apollo11, started a minute ago. (id: e7ccd52)
```

### cancel

Cancel the last call to the start command. The time will not
be recorded.

### status

Display the time spent since the current project was started.

```
$ watson status
Project apollo11 started seconds ago
```

### report

Display a report of the time spent on each project.

If a project is given, the time spent on this project is printed. Else,
print the total for each root project.

By default, the time spent the last 7 days is printed. This timespan
can be controlled with the `--from` and `--to` arguments. The dates
must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

You can limit the report to a project or a tag using the `--project` and
`--tag` options. They can be specified several times each to add multiple
projects or tags to the report.


```
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
```

### log

Display each recorded frames during the given timespan.

By default, the frames from the last 7 days are printed. This timespan
can be controlled with the `--from` and `--to` arguments. The dates
must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

You can limit the log to a project or a tag using the `--project` and
`--tag` options. They can be specified several times each to add multiple
projects or tags to the log.

```
$ watson log
Thursday 08 May 2015
        f35bb24  09:26 to 10:22     56m 33s  apollo11  [reactor, brakes, steering, wheels, module]

Wednesday 07 May 2015
        9a1325d  09:48 to 10:15     27m 29s  voyager2  [sensors, generators, probe]

Tuesday 06 May 2015
        530768b  12:40 to 14:16  1h 35m 45s  apollo11  [wheels]
        84164f0  14:23 to 14:35     11m 37s  apollo11  [brakes, steering]

Monday 05 May 2015
        26a2817  09:05 to 10:03     57m 12s  voyager2  [probe, generators]
        5590aca  10:51 to 14:47  3h 55m 40s  apollo11
        c32c74e  15:12 to 18:38  3h 25m 34s  voyager2  [probe, generators, sensors, antenna]


$ watson log --from 2014-04-16 --to 2014-04-17
Thursday 17 April 2014
        a96fcde  09:15 to 09:43     28m 11s    hubble  [lens, camera, transmission]
        5e91316  10:19 to 12:59  2h 39m 15s    hubble  [camera, transmission]
        761dd51  14:42 to 15:54  1h 11m 47s  voyager1  [antenna]

Wednesday 16 April 2014
        02cb269  09:53 to 12:43  2h 50m 07s  apollo11  [wheels]
        1070ddb  13:48 to 16:17  2h 29m 11s  voyager1  [antenna, sensors]
```

### frames
Display the list of all frame IDs.

This is mainly useful for implementing Bash command line completion.

```
$ watson frames
f1c4815
9d1a989
8801ec3
[...]
```

### projects

Display the list of all existing projects.

```
$ watson projects
apollo11
hubble
voyager1
voyager2
```

### edit

Edit a frame. You can get the id of a frame with the `watson log` command.
If no id is given, defaults to the last recorded frame.

The `$EDITOR` environment variable is used to detect your editor.

### remove

Remove a frame.

### config

Get and set configuration options.

If value is not provided, the content of the key is displayed. Else,
the given value is set.

You can edit the configuration file with an editor with the '--edit' option.

```
$ watson config backend.token 7e329263e329
$ watson config backend.token
7e329263e329
```

### sync

Get frames from the server and push the new ones.

**Warning:** this feature is still experimental and not yet publicly available.

> In a near future, you will be able to sync Watson with your [artich.io](https://artich.io/?pk_campaign=GitHubWatson) account or any compatible third-party back-end.

The URL of the server and the User Token must be defined in your [configuration file](#configuration) or with the [`config`](#config) command.

```
$ watson config backend.url http://localhost:4242
$ watson config backend.token 7e329263e329
$ watson sync
Received 42 frames from the server
Pushed 23 frames to the server
```

## Configuration

The configuration and the data are stored inside your user's application folder.

On Mac, this is `~/Library/Application Support/watson/config`, on Windows this is
`C:\Users\<user>\AppData\Local\watson\config` and on Linux `~/.config/watson/config`.

If you want to edit your configuration, the best is to use the
[`config`](#config) command.

### Deleting all your frames

If you want to remove all your frames, you can delete the `frames` file in your
configuration folder (see above to find its location).
