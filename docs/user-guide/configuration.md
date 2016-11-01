# Configuration

## The configuration file

Watson configuration and data are stored inside your user's application folder. Depending on your system, the default path might be:

* **MacOSX**: `~/Library/Application Support/watson/config`
* **Windows**: `C:\Users\<user>\AppData\Local\watson\config`
* **Linux**: `~/.config/watson/config`

The configuration file is a typical [python configuration (INI) file](https://docs.python.org/3.4/library/configparser.html#supported-ini-file-structure), that looks like:

```ini
[Simple Values]
key=value
spaces in keys=allowed
spaces in values=allowed as well
spaces around the delimiter = obviously
you can also use : to delimit keys from values

[All Values Are Strings]
values like this: 1000000
or this: 3.14159265359
are they treated as numbers? : no
integers, floats and booleans are held as: strings
can use the API to get converted values directly: true

[Multiline Values]
chorus: I'm a lumberjack, and I'm okay
    I sleep all night and I work all day


[No Values]
key_without_value
empty string value here =

[You can use comments]
# like this
; or this

# By default only in an empty line.
# Inline comments can be harmful because they prevent users
# from using the delimiting characters as parts of values.
# That being said, this can be customized.

    [Sections Can Be Indented]
        can_values_be_as_well = True
        does_that_mean_anything_special = False
        purpose = formatting for readability
        multiline_values = are
            handled just fine as
            long as they are indented
            deeper than the first line
            of a value
        # Did I mention we can indent comments, too?
```

_This example configuration file has been taken from the [official python documentation](https://docs.python.org/3.4/library/configparser.html#supported-ini-file-structure)._


## Editing

If you want to edit your configuration, the best is to use the [`config`](./commands/#config) command.

You can edit your configuration on the fly with:

```bash
$ watson config SECTION.KEY VALUE
```

Example:

```bash
$ watson config backend.token 7e329263e329  # set configuration
$ watson config backend.token  # display configuration
7e329263e329
```

Or open an editor with:

```bash
$ watson config -e
```

## Available settings

### Backend

At this time there is no official backend for Watson. We are working on it. But in a near future, you will be able to synchronize Watson with a public (or your private) repository via the [`sync`](./commands.md#sync) command. To configure your repository please set up the `[backend]` section.

#### `backend.url`

This is the API root url of your repository, e.g. `https://my.server.com/api/`

#### `backend.token`

To authenticate watson as an API client, once generated, you will need to set up your API token in your configuration, e.g. `7e329263e329`.

### Options

#### `options.log_current`

If `true`, the output of the `log` command will include the currently running
frame (if any) by default. The option can be overridden on the command line
with the `-c/-C` resp. `--current/--no-current` flags.

#### `options.report_current`

If `true`, the output of the `report` command will include the currently
running frame (if any) by default. The option can be overridden on the
command line with the `-c/-C` resp. `--current/--no-current` flags.

#### `options.stop_on_start`

If `true`, starting a new project will stop running projects:

```
$ watson start samourai +pizza +cat
Starting project samourai [pizza, cat] at 11:14
$ watson start jayce +wheeled +warriors
Stopping project samourai [pizza, cat], started 2 minutes ago. (id: d08cdd0)
Starting project jayce [wheeled, warriors] at 11:16
```

Please, note that it also works with serious stuffs like:

```
$ watson start voyager2 +reactor +module
Stopping project jayce [wheeled, warriors], started 2 minutes ago. (id: 967965f)
Starting project voyager2 [reactor, module] at 11:18
```

#### `options.stop_on_restart`

Similar to the `options.stop_on_start` option, but for the [`restart`](./commands.md#restart) command.

#### `options.date_format`

Globally configure how `dates` should be formatted. All [python's `strftime` directives](http://strftime.org) are supported.

#### `options.time_format`

Globally configure how `time` should be formatted. All [python's `strftime` directives](http://strftime.org) are supported.

### Default tags

Tags can be automatically added for selected projects. This is convenient when
the same tags are always attached to a particular project.

These automatically attached tags are defined in the `[default_tags]` section
of the configuration. Each option in that section is a project to which
tags should be attached. The entries should follow the pattern: `project = tag1 tag2`.

You can set default tags for a project from the command line:

```
$ watson config default_tags.python101 'teaching python'
```

This corresponds to the following configuration file snippets:

```ini
[default_tags]
python101 = teaching python
```

With these default tags set, the tags "teaching" and "python" will
automatically be attached to the project "python101":

```
$ watson start python101
Starting project python101 [teaching, python] at 19:27

$ watson start python101 +lecture
Starting project python101 [lecture, teaching, python] at 19:28
```

Default tags can contain space characters when written in between quotes:

```
$ watson config default_tags.voyager2 'nasa "space mission"'
```

Or in the configuration file:

```ini
[default_tags]
voyager2 = nasa 'space mission'
```

## Sample configuration file

A basic configuration file looks like the following:

```ini
# Watson configuration

[backend]
url = https://api.crick.fr
token = yourapitoken

[options]
stop_on_start = true
stop_on_restart = false
date_format = %Y.%m.%d
time_format = %H:%M:%S%z
log_current = false
report_current = false
```

## Application folder

To override Watson's default application folder (see first section), you can set the `$WATSON_DIR` environment variable to the desired path.

It may be defined globally in your shell profile:

```bash
# .bashrc or .profile
export WATSON_DIR=/path/to/watson/folder
```

or when calling Watson:

```bash
$ WATSON_DIR=/path/to/watson/folder watson status
```

This can be useful to preserve your real data when hacking with Watson :)
