Watson
======

Watson is a tool aimed at helping you monitoring your time.

You just have to tell Watson when you start working on your
project with the `start` command, and you can stop the timer
when you're done with the `stop` command.

Projects can be divided in sub-projects by giving the projet and
the name of the sub-projects to the `start` command.

## Commands

### start

Start monitoring the time for the given project.

You can specify sub-projects by separating each name by
slashes (`/`) or spaces.

```
Example :
$ watson start apollo11 reactor
Starting apollo11/reactor at 16:34
```

### stop

Stop monitoring time for the current project

```
$ watson stop
Stopping project apollo11/reactor, started a minute ago
```

### cancel

Cancel the last call to the start command. The time will not
be recorded.

### status

Display the time spent since the current project was started.

```
$ watson status
Project apollo11/reactor started seconds ago
```

### log
Display a summary of the time spent on each project.

If a project is given, the time spent on this project and
each subproject is printed. Else, print the total for each root
project.

By default, the time spent the last 7 days is printed. This timespan
can be controlled with the `--from` and `--to` arguments. The dates
must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

```
$ watson log
Mon 05 May 2014 -> Mon 12 May 2014

 23h 53m 16s apollo11
  7h 06m 08s hubble
  1h 06m 53s voyager1
 12h 19m 53s voyager2

Total: 44h 26m 10s

$ watson log --from 2014-04-01 --to 2014-04-30  apollo11
Tue 01 April 2014 -> Wed 30 April 2014

  1h 32m 54s apollo11
  8h 28m 09s apollo11/lander
 14h 15m 07s apollo11/lander/brakes
  9h 37m 34s apollo11/lander/parachute
 11h 04m 39s apollo11/lander/steering
  6h 23m 38s apollo11/lander/wheels
  3h 28m 44s apollo11/module
 11h 23m 27s apollo11/reactor

Total: 66h 14m 12s
```

### report

Print a report of the time spent on projects during the given timespan.

By default, the time spent the last 7 days is printed. This timespan
can be controlled with the `--from` and `--to` arguments. The dates
must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

```
$ watson report
Monday 05 May 2014
        09:21 to 12:39  apollo11/reactor  3h 17m 58s
        13:26 to 14:05  voyager2/probe/generators 39m 08s
        14:37 to 17:11  hubble/transmission  2h 33m 12s

Tuesday 06 May 2014
        09:38 to 10:40  voyager1/launcher  1h 02m 37s
        10:48 to 11:36  hubble/lens 48m 51s
        12:17 to 12:35  voyager2/launcher 17m 43s
        12:39 to 16:15  voyager1/launcher  3h 35m 35s
        16:50 to 17:51  hubble/lens  1h 00m 29s

Wednesday 07 May 2014
        09:43 to 12:55  apollo11/lander  3h 11m 37s
        13:34 to 15:07  apollo11  1h 32m 54s
        15:43 to 18:17  apollo11/reactor  2h 33m 59s

Thursday 08 May 2014
        09:36 to 13:33  hubble  3h 56m 32s
        14:05 to 15:37  voyager1/probe/generators  1h 31m 58s
        16:33 to 20:14  voyager1/probe/sensors  3h 41m 07s

Friday 09 May 2014
        09:30 to 13:06  voyager2/probe  3h 36m 46s
        13:37 to 15:31  voyager2/probe  1h 54m 01s

$ watson report --from 2014-04-16 --to 2014-04-18
Wednesday 16 April 2014
        09:52 to 13:21  apollo11/module  3h 28m 58s
        14:01 to 14:42  apollo11/lander/brakes 41m 00s
        14:46 to 17:27  voyager2/probe/antenna  2h 40m 59s

Thursday 17 April 2014
        09:18 to 10:12  voyager2 53m 54s
        10:19 to 12:40  voyager1/probe  2h 20m 49s
        12:51 to 14:31  hubble/camera  1h 39m 22s
        15:11 to 15:40  voyager2/probe/antenna 29m 33s
        15:42 to 16:25  voyager2/probe/antenna 42m 40s
        16:46 to 18:26  apollo11/reactor  1h 39m 29s

Friday 18 April 2014
        09:55 to 13:39  voyager1/probe/sensors  3h 43m 51s
        14:29 to 14:45  hubble/camera 15m 20s
        14:55 to 16:32  voyager2  1h 36m 19s
        17:18 to 20:04  hubble/lens  2h 45m 07s
```

### projects

Display the list of all the existing projects.

```
$ watson projects
apollo11
apollo11/reactor
apollo11/module
apollo11/lander
hubble
voyager1
voyager2
```

### config
Get and set configuration options.

If value is not provided, the content of the key is displayed. Else,
the given value is set.

You can edit the config file with an editor with the '--edit' option.

```
$ watson config crick.token 7e329263e329
$ watson config crick.token
7e329263e329
```

### sync
Get the frames from the server and push the new ones.

The URL of the server and the User Token must be defined in a `.watson.conf` file
placed inside your user directory.

```
$ watson config crick.url http://localhost:4242
$ watson config crick.token 7e329263e329
$ watson sync
Received 42 frames from the server
Pushed 23 frames to the server
```

See [django-crick](https://bitbucket.org/tailordev/django-crick) for more information.


## import
Import a file containing frames. Currently only ICS (and Ical) files are
supported.

```
$ watson import calendar.ics
Imported 42 frames.
```
