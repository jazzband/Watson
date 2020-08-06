.. image:: https://tailordev.github.io/Watson/img/logo-watson-600px.png

|Build Status| |PyPI Latest Version| |Requires.io|

Watson is here to help you manage your time. You want to know how
much time you are spending on your projects? You want to generate a nice
report for your client? Watson is here for you.

Wanna know what it looks like? Check this below.

|Watson screenshot|_

Nice isn't it?

Quick start
-----------

Installation
~~~~~~~~~~~~

On OS X, the easiest way to install **watson** is using `Homebrew <http://brew.sh/>`_:

.. code:: bash

  $ brew update && brew install watson

On other platforms, install **watson** using pip or pip3, depending on which one is available:

.. code:: bash

  $ pip install td-watson

or:

.. code:: bash

  $ pip3 install td-watson

If you need more details about installing watson, please refer to the `documentation <https://tailordev.github.io/Watson>`_.

Usage
~~~~~

Start tracking your activity via:

.. code:: bash

  $ watson start world-domination +cats

With this command, you have started a new **frame** for the *world-domination* project with the *cats* tag. That's it.

Now stop tracking you world domination plan via:

.. code:: bash

  $ watson stop
  Project world-domination [cats] started 8 minutes ago (2016.01.27 13:00:28+0100)

You can log your latest working sessions (aka **frames**) thanks to the ``log`` command:

.. code:: bash

  $ watson log
  Tuesday 26 January 2016 (8m 32s)
        ffb2a4c  13:00 to 13:08      08m 32s   world-domination  [cats]

Please note that, as `the report command <https://tailordev.github.io/Watson/user-guide/commands/#report>`_, the ``log`` command comes with projects, tags and dates filtering.

To list all available commands, either `read the documentation <https://tailordev.github.io/Watson>`_ or use:

.. code:: bash

  $ watson help

Contributor Code of Conduct
---------------------------

If you want to contribute to this project, please read the project `Contributor Code of Conduct <https://tailordev.github.io/Watson/contributing/coc/>`_

License
-------

Watson is released under the MIT License. See the bundled LICENSE file for
details.

.. |Build Status| image:: https://travis-ci.org/TailorDev/Watson.svg?branch=master
   :target: https://travis-ci.org/TailorDev/Watson
.. |PyPI Latest Version| image:: https://img.shields.io/pypi/v/td-watson.svg
   :target: https://pypi.python.org/pypi/td-watson
.. |Requires.io| image:: https://requires.io/github/TailorDev/Watson/requirements.svg?branch=master
   :target: https://requires.io/github/TailorDev/Watson/requirements/?branch=master
   :alt: Requirements Status
.. |Watson screenshot| image:: https://tailordev.github.io/Watson/img/watson-demo.gif
.. _Watson screenshot: https://asciinema.org/a/35918
