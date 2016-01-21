Contributing
############

If you are reading this, we thank you in advance for willing to contribute to the Watson project! You are awesome.

.. Disclaimer::

    This document is heavily inspired by `Kinto's project documentation<https://github.com/Kinto/kinto>`_ Thank them for providing high quality content for the community.


How to contribute
=================

Report bugs
-----------

Report bugs at https://github.com/TailorDev/Watson/issues/new

If you are reporting a bug, please include:

* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix bugs
--------

Check out the `open bugs <https://github.com/TailorDev/Watson/issues>`_ - anything tagged with the **[easy-pick]** label could be a good choice for newcomers.

Implement features
------------------

Look through the GitHub issues for features. Anything tagged with **[enhancement]** is open to whoever wants to implement it.

Write documentation
-------------------

*Watson* could always use more documentation, whether as part of the official docs, in docstrings, or even on the Web in blog posts, articles, and such.

Submit feedback
---------------

Any issue with the **[question]** label is open for feedback, so feel free to
share your thoughts with us!

The best way to send feedback is to `fill a new issue <https://github.com/TailorDev/Watson/issues/new>`_ on GitHub.

If you are proposing a feature:

* Explain how you envision it working. Try to be as detailed as you can.
* Try to keep the scope as narrow as possible. This will help make it easier
  to implement.
* Feel free to include any code you might already have, even if it's just a
  rough idea. This is a volunteer-driven project, and contributions
  are welcome :)

Hack
====

Ready to contribute? Here's how to set up *Watson* for local development.

Get started!
------------

1. Fork the *Watson* repo on GitHub.

2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/Watson.git

3. Install *Watson* locally::

    $ mkvirtualenv watson
    $ cd Watson
    $ python setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass the tests::

    $ py.test

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.


Pull request guidelines
-----------------------

.. note::

    Open a pull-request even if your contribution is not ready yet! It can
    be discussed and improved collaboratively!

Before we merge a pull request, we check that it meets these guidelines:

1. The pull request should include tests.
2. If the pull request adds functionality, the docs should be updated.
3. *TravisCI* integration tests should be *green* :) It will make sure the tests pass with every supported version of Python.
