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

### push

Push all the new frames to a Crick server.

The URL of the server and the User Token must be defined in a `.watson.conf` file
placed inside your user directory.

If you give the '-f' (or '--force') flag to the command, it will
also update all the existing frames on the server.

```
$ watson config crick.url http://localhost:4242
$ watson config crick.token 7e329263e329
$ watson push
```

See [django-crick](https://bitbucket.org/tailordev/django-crick) for more information.
