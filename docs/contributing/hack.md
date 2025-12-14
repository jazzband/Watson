# Hack

Ready to contribute? Here's how to set up *Watson* for local development.

## Python requirements

- Python 3.10+
- [UV](https://docs.astral.sh/uv/) package manager

## Get started!

1. Fork the [Watson repository](https://github.com/jazzband/Watson/) on GitHub.

2. Clone your fork locally:

        $ git clone git@github.com:your_name_here/Watson.git

3. Create a virtual environment and install project dependencies:

        $ cd Watson
        $ make bootstrap

5. Create a branch for local development:

        $ git checkout -b name-of-your-bugfix-or-feature

    Now you can make your changes locally.

    _Notes:_

    - The files you need to edit to change watson's behavior are located in the
      `watson/` subfolder.
    - Every time you run `watson` inside the virtual environment, the source
      code inside the `watson/` subfolder will be used.
    - To avoid messing with your real Watson data, watson will use `data/` as
      the [application folder](../user-guide/configuration.md/#application-folder)
      inside the virtual environment. You can run `watson projects` to check
      that your real projects are not shown.

6. When you're done making changes, check that your changes pass the tests
    (see [Run the tests](#run-the-tests)):

        (.venv) $ tox

7. If you have added a new command or updated/fixed docstrings, please update
    the documentation. You can check changes live using:

        $ make docs-serve

8. Commit your changes and push your branch to GitHub:

        $ git add .
        $ git commit -m "Your detailed description of your changes."
        $ git push -u origin name-of-your-bugfix-or-feature

9. After [reading this](./pr-guidelines.md), submit a pull request through the
    GitHub website.

<a href="#run-the-tests"></a>
## Run the tests

The tests use [pytest](http://pytest.org/). To run them with the default Python
interpreter run:

    $ make test 

If you want to run pytest with custom options, use:

    $ uv run pytest -x -k test_cli
