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
