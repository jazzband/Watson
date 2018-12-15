# Hack

Ready to contribute? Here's how to set up *Watson* for local development.

## Get started!

1.  Fork the [Watson repository](https://github.com/TailorDev/Watson/) on GitHub.
2.  Clone your fork locally:

        $ git clone git@github.com:your_name_here/Watson.git

3.  Install Watson locally:

        $ mkvirtualenv watson
        $ cd Watson
        $ pip install -r requirements-dev.txt
        $ python setup.py develop
    
    A few notes:

      - Beware that, depending on your configuration, your virtual environment
        may be created in a centralized location (like `$HOME/.virtualenvs`),
        and not in the current folder.
      
      - Also, beware that changing the names of the folders pointing to this
        development folder may give an undesired behavior.
      
      - It is probably a good idea to copy (at least) some of your existing
        watson frames into your new development folder, to test your changes:
      
            $ cp -R ~/.config/watson ./data/
      
        To make these used by watson, it is necessary to set the `WATSON_DIR`
        variable. It can be set with:
      
            $ export WATSON_DIR=$PWD/data
      
        It may be a good idea to modify the `bin/activate` file from your virtualenv
        (either `venv/bin/activate` or `$HOME/.virtualenvs/watson/bin/activate`),
        and add the following lines (just before the `PATH` settings, for instance):
        
            WATSON_DIR=$PWD/data
            export WATSON_DIR
        
        This will be set each time you start the virtualenv and you will not have to
        re-set the variable each time.

4.  Create a branch for local development:

        $ git checkout -b name-of-your-bugfix-or-feature

    Now you can make your changes locally.
    
    The files you need to edit to change watson's behavior are located in the
    `watson/` subfolder. 
    
    To test, you can add a word or two in the sentences output by the `watson
    status` command (for instance, modify the "No project started" string in
    `watson/cli.py`). Save your modifications, type `watson status`. If you can
    see the words you added, you are ready to hack (congratulations!). You may
    revert to the original version of `watson/cli.py` with `git checkout
    watson/cli.py`.
    
5.  When you're done making changes, check that your changes pass the tests
    (see [Run the tests](#run-the-tests)):

        $ tox

6. If you have added a new command or updated/fixed docstrings, please update the documentation:

        $ make docs
   
     Beware that mkdocs 0.14 is not compatible with Python 3.7: you should either
     use a virtualenv with Python 3.6 or update `mkdocs` to a more recent version
     (1.0.4 at the time of writing, which also requires running `pip install
     --upgrade mkdocs-bootstrap mkdocs-bootswatch` to get the `flatly` theme
     used by our docs). 

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
