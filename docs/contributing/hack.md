# Hack

Ready to contribute? Here's how to set up *Watson* for local development.

## Python requirements
* Python (2/3) interpreter installed
* `pip` tool to install package dependencies
* `virtualenv` tool to create virtual environments

## Get started!

1. Fork the [Watson repository](https://github.com/TailorDev/Watson/) on GitHub.

2. Clone your fork locally:

        $ git clone git@github.com:your_name_here/Watson.git

3. Create a virtual environment:

        $ cd Watson
        $ make env

    The Python version used will be the one accessible using the `python`
    command in your shell.

    To use a different Python version, define the `PYTHON` shell variable.
    For example:

        $ PYTHON=python3.5 make env

4. Install dependencies and deploy Watson inside the virtual environment:

        $ source .venv/bin/activate
        (.venv) $ make install-dev

    If you are using fish shell, source `.venv/bin/activate.fish` instead.

5. Create a branch for local development:

        (.venv) $ git checkout -b name-of-your-bugfix-or-feature

    Now you can make your changes locally.

    _Notes:_

    - The files you need to edit to change watson's behavior are located in the
      `watson/` subfolder.
    - Every time you run `watson` inside the virtual environment, the source
      code inside the `watson/` subfolder will be used.
    - To avoid messing with your real Watson data, watson will use `data/` as
      the [application folder](../user-guide/configuration/#application-folder)
      inside the virtual environment. You can run `watson projects` to check
      that your real projects are not shown.

6. When you're done making changes, check that your changes pass the tests
    (see [Run the tests](#run-the-tests)):

        (.venv) $ tox

7. If you have added a new command or updated/fixed docstrings, please update
    the documentation:

        (.venv) $ make docs

8. Commit your changes and push your branch to GitHub:

        $ git add .
        $ git commit -m "Your detailed description of your changes."
        $ git push -u origin name-of-your-bugfix-or-feature

9. After [reading this](./pr-guidelines.md), submit a pull request through the
    GitHub website.

<a href="#run-the-tests"></a>
## Run the tests

The tests use [pytest](http://pytest.org/). To run them with the default Python
interpreter:

    $ py.test -v tests/

To run the tests via [tox](http://tox.testrun.org/) with all Python versions
which are available on your system and are defined in the `tox.ini` file,
simply run:

    $ tox

This will also check the source code with [flake8](http://flake8.pycqa.org).
