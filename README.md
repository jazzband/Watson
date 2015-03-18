Watson [![Build Status](https://travis-ci.org/TailorDev/Watson.svg)](https://travis-ci.org/TailorDev/Watson)
======

Watson is a tool aimed at helping you monitoring your time.

You just have to tell Watson when you start working on your
project with the `start` command, and you can stop the timer
when you're done with the `stop` command.

## Commands

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

14h 51m 35s apollo11
        [14h 49m 46s brakes]
        [ 8h 58m 20s module]
        [10h 01m 20s reactor]
        [12h 39m 40s steering]
        [11h 34m 51s wheels]
11h 34m 36s hubble
        [ 8h 07m 26s camera]
        [ 7h 59m 32s lens]
        [ 9h 20m 33s transmission]
 7h 47m 41s voyager1
        [ 1h 25m 32s antenna]
        [ 1h 25m 32s generators]
        [ 1h 25m 32s probe]
 9h 28m 28s voyager2
        [ 5h 31m 48s antenna]
        [ 9h 08m 25s generators]
        [ 2h 43m 03s probe]
        [ 5h 51m 51s sensors]

Total: 43h 42m 20s


$ watson log --from 2014-04-01 --to 2014-04-30  apollo11
Tue 01 April 2014 -> Wed 30 April 2014

39h 44m 06s apollo11
        [17h 49m 47s brakes]
        [10h 12m 06s module]
        [22h 44m 33s reactor]
        [14h 08m 04s steering]
        [11h 19m 01s wheels]
```

### report

Print a report of the time spent on projects during the given timespan.

By default, the time spent the last 7 days is printed. This timespan
can be controlled with the `--from` and `--to` arguments. The dates
must have the format `YEAR-MONTH-DAY`, like: `2014-05-19`.

```
$ watson report
Monday 05 May 2014
        a7f8157  09:57 to 12:05  apollo11  2h 08m 34s
        44866f1  12:32 to 16:21  voyager2  3h 48m 59s
        4864459  16:36 to 19:12  voyager2 [antenna]  2h 35m 07s

Tuesday 06 May 2014
        3142104  09:49 to 12:49  voyager2 [sensors]  2h 59m 20s
        8c99d9e  13:03 to 14:43  voyager2 [antenna, sensors]  1h 39m 45s
        0469b72  15:41 to 18:40  voyager2 [antenna, probe]  2h 59m 03s

Wednesday 07 May 2014
        0d2be24  09:16 to 10:53  apollo11 [reactor, steering]  1h 36m 53s
        0ae6308  11:41 to 14:21  apollo11 [wheels, brakes]  2h 39m 53s
        a62ac93  14:35 to 18:27  hubble  3h 52m 12s

Thursday 08 May 2014
        b4f3d47  09:34 to 11:29  voyager2 [generators, probe]  1h 55m 01s
        ae68bf6  11:45 to 15:37  hubble [lens, transmission]  3h 52m 10s
        501e43a  16:21 to 16:48  hubble [lens, camera] 27m 03s
        7c31426  17:30 to 18:39  voyager2 [sensors, probe]  1h 08m 59s


$ watson report --from 2014-04-16 --to 2014-04-17
Wednesday 16 April 2014
        c983586  09:28 to 12:55  apollo11  3h 26m 12s
        1a5dbe5  13:52 to 14:51  voyager2 [sensors, antenna] 58m 21s
        478ad13  15:44 to 16:52  hubble [transmission]  1h 07m 43s

Thursday 17 April 2014
        a57e276  09:29 to 12:33  voyager1 [antenna, probe]  3h 04m 45s
        8f25306  13:03 to 13:15  voyager1 11m 53s
        975c6f6  13:46 to 17:34  apollo11 [reactor]  3h 47m 29s
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

See [Crick](http://crick.fr) for more information.
