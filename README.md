![Watson Logo](https://jazzband.github.io/Watson/img/logo-watson.svg)

![PyPI - Version](https://img.shields.io/pypi/v/td-watson)

Watson is here to help you manage your time. You want to know how much time you
are spending on your projects? You want to generate a nice report for your
client? Watson is here for you.

Wanna know what it looks like? Check this below.

[
![](https://jazzband.github.io/Watson/img/watson-demo.gif)
](https://asciinema.org/a/35918)

Nice isn't it?

## Quick start

### Installation

The easiest way to install Watson is to use [uv](https://docs.astral.sh/uv/):

```sh
$ uv tool install td-watson
```

This will create a Python virtual environment for Watson and a shortcut
available in your `$PATH`.

Alternatively, you may use Pip instead (in a virtual environment):

```sh
$ pip install --user td-watson
```

On OS X, a [Homebrew](http://brew.sh/) formula is also available:

```sh
$ brew update && brew install watson
```

If you need more details about installing watson, please refer to the
[documentation](https://jazzband.github.io/Watson)

### Usage

Start tracking your activity via:

```sh
$ watson start world-domination +cats
```

With this command, you have started a new **frame** for the *world-domination*
project with the *cats* tag. That's it.

Now stop tracking you world domination plan via:


```sh
$ watson stop
Project world-domination [cats] started 8 minutes ago (2016.01.27 13:00:28+0100)
```

You can log your latest working sessions (aka *frames*) thanks to the `log`
command:


```sh
$ watson log
Tuesday 26 January 2016 (8m 32s)
      ffb2a4c  13:00 to 13:08      08m 32s   world-domination  [cats]
```

Please note that, as [the report
command](https://tailordev.github.io/Watson/user-guide/commands/#report), the
`log` command comes with projects, tags and dates filtering.

To list all available commands, either [read the
documentation](https://tailordev.github.io/Watson) or use:


```sh
$ watson help
```

## Contributor Code of Conduct

If you want to contribute to this project, please read the project [Contributor
Code of Conduct](https://tailordev.github.io/Watson/contributing/coc/)

## License

Watson is released under the MIT License. See the bundled LICENSE file for
details.
