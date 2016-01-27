Watson
======

|Build Status| |PyPI Downloads Per Month| |PyPI Latest Version| |Requires.io|

Watson is here to help you monitoring your time. You want to know how
much time you are spending on your projects? You want to generate a nice
report for your client? Watson is here for you.

Wanna know what it looks like? Check this below.

![screenshot](docs/img/screenshot.png)

Nice isn't it?

Quick start
-----------

Installation
~~~~~~~~~~~~

.. code:: bash

  $ pip install td-watson

If you need more details about installing watson, please refer to its `documentation <https://tailordev.github.io/Watson>`_.

Usage
~~~~~

Start tracking your activity via:

.. code:: bash

  $ watson start world-domination +cats

With this command, you have started a new **frame** for the *world-domination* project with the *cat* tag. That's it.

Now stop tracking you world domination plan via:

.. code:: bash

  $ watson stop
  Project world-domination [cat] started 8 minutes ago (2016.01.27 13:00:28+0100)

To list all available commands, either `read the documentation <https://tailordev.github.io/Watson>`_ or use:

.. code:: bash

  $ watson help

Contributor Code of Conduct
---------------------------

As contributors and maintainers of this project, we pledge to respect all
people who contribute through reporting issues, posting feature requests,
updating documentation, submitting pull requests or patches, and other
activities.

We are committed to making participation in this project a harassment-free
experience for everyone, regardless of level of experience, gender, gender
identity and expression, sexual orientation, disability, personal appearance,
body size, race, age, or religion.

Examples of unacceptable behavior by participants include the use of sexual
language or imagery, derogatory comments or personal attacks, trolling, public
or private harassment, insults, or other unprofessional conduct.

Project maintainers have the right and responsibility to remove, edit, or
reject comments, commits, code, wiki edits, issues, and other contributions
that are not aligned to this Code of Conduct. Project maintainers who do not
follow the Code of Conduct may be removed from the project team.

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by opening an issue or contacting one or more of the project
maintainers.

This Code of Conduct is adapted from the `Contributor Covenant
<http:contributor-covenant.org>`__, version 1.0.0, available at
`http://contributor-covenant.org/version/1/0/0/
<http://contributor-covenant.org/version/1/0/0/>`__.

License
-------

Watson is released under the MIT License. See the bundled LICENSE file for
details.

.. |Build Status| image:: https://travis-ci.org/TailorDev/Watson.svg?branch=master
   :target: https://travis-ci.org/TailorDev/Watson
.. |PyPI Downloads Per Month| image:: https://img.shields.io/pypi/dm/td-watson.svg
   :target: https://pypi.python.org/pypi/td-watson
.. |PyPI Latest Version| image:: https://img.shields.io/pypi/v/td-watson.svg
   :target: https://pypi.python.org/pypi/td-watson
.. |Requires.io| image:: https://requires.io/github/TailorDev/Watson/requirements.svg?branch=master
   :target: https://requires.io/github/TailorDev/Watson/requirements/?branch=master
   :alt: Requirements Status
