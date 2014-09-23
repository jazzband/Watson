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

### push

Push all the new frames to a Crick server.

The URL of the server and the User Token must be defined in a `.watson.conf` file
placed inside your directory.

Example of `.watson.conf` file:
```
[crick]
url = http://localhost:4242
token = 7e329263e329646be79d6cc3b3af7bf48b6b1779
```

See [django-crick](https://bitbucket.org/tailordev/django-crick) for more information.
