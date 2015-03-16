Watson
======

Watson is a tool aimed at helping you monitoring your time.

You just have to tell Watson when you start working on your
project with the `start` command, and you can stop the timer
when you're done with the `stop` command.

## Commands

### start

Start monitoring the time for the given project.

```
Example :
$ watson start apollo11 reactor
Starting apollo11 at 16:34
```

### stop

Stop monitoring time for the current project

```
$ watson stop
Stopping project apollo11, started a minute ago
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

### log
Display a summary of the time spent on each project.

If a project is given, the time spent on this project is printed. Else,
print the total for each root project.

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

Total: 1h 32m 54s
```

### report

Print a report of the time spent on projects during the given timespan.

By default, the time spent the last 7 days is printed. This timespan
can be controlled with the `--from` and `--to` arguments. The dates
must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

```
$ watson report
Monday 05 May 2014
        09:21 to 12:39  apollo11  3h 17m 58s
        13:26 to 14:05  voyager2 39m 08s
        14:37 to 17:11  hubble  2h 33m 12s

Tuesday 06 May 2014
        09:38 to 10:40  voyager1  1h 02m 37s
        10:48 to 11:36  hubble 48m 51s
        12:17 to 12:35  voyager2 17m 43s

Wednesday 07 May 2014
        09:43 to 12:55  apollo11  3h 11m 37s

Thursday 08 May 2014
        09:36 to 13:33  hubble  3h 56m 32s
        16:33 to 20:14  voyager1  3h 41m 07s

Friday 09 May 2014
        09:30 to 13:06  voyager2  3h 36m 46s

$ watson report --from 2014-04-16 --to 2014-04-18
Wednesday 16 April 2014
        14:01 to 14:42  apollo11 41m 00s
        14:46 to 17:27  voyager2  2h 40m 59s

Thursday 17 April 2014
        09:18 to 10:12  voyager2 53m 54s
        10:19 to 12:40  voyager1  2h 20m 49s
        12:51 to 14:31  hubble  1h 39m 22s
        16:46 to 18:26  apollo11  1h 39m 29s

Friday 18 April 2014
        09:55 to 13:39  voyager1  3h 43m 51s
        14:29 to 14:45  hubble 15m 20s
        14:55 to 16:32  voyager2  1h 36m 19s
```

### projects

Display the list of all the existing projects.

```
$ watson projects
apollo11
hubble
voyager1
voyager2
```

### edit

Edit a frame. You can get the id of a frame with the `watson report`
command.

The `$EDITOR` environment variable is used to detect your editor.

### remove

Remove a frame.

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
