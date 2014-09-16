Watson
======

Watson is a tool aimed at helping you monitoring your time.

You just have to tell Watson when you start working on your
project with the `start` command, and you can stop the timer
when you're done with the `stop` command.

Projects can be divided in sub-projects by giving the projet and
the name of the sub-project to the `start` command.

## Commands

### start

Start monitoring the time for the given project.

You can specify a subproject by separating the project
and the subproject by either a space or a `/`.

```
$ watson start apollo11/reactor
Starting apollo11/reactor at 16:34
```

### stop

Stop monitoring time for the current project or subproject

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
