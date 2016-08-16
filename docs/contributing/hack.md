# Hack

Ready to contribute? Here's how to set up *Watson* for local development.

## Get started!

1.  Fork the [Watson repository](https://github.com/TailorDev/Watson/) on GitHub.
2.  Clone your fork locally:

        $ git clone git@github.com:your_name_here/Watson.git

3.  Install Watson locally:

        $ mkvirtualenv watson
        $ cd Watson
        $ pip install -r requirements-tests.txt
        $ python setup.py develop

4.  Create a branch for local development:

        $ git checkout -b name-of-your-bugfix-or-feature

    Now you can make your changes locally.

5.  When you're done making changes, check that your changes pass the tests
    (see [Run the tests](#run-the-tests)):

        $ tox

6. If you have added a new command or updated/fixed docstrings, please update the documentation:

        $ make docs

7.  Commit your changes and push your branch to GitHub:

        $ git add .
        $ git commit -m "Your detailed description of your changes."
        $ git push -u origin name-of-your-bugfix-or-feature

8.  After [reading this](./pr-guidelines.md), submit a pull request through the GitHub website.


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
