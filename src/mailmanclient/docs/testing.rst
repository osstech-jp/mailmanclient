========================
Developing MailmanClient
========================


Running Tests
=============

The test suite is run with the `tox`_ tool, which allows it to be run against
multiple versions of Python. The tests are discovered and run using `pytest`_.

To run the test suite, run::

  $ tox

To run tests for only one version of Python, you can run::

  $ tox -e py39
  
``pytest`` starts Mailman Core using ``pytest-services`` plugin and
automatically manages it's start and stop cycle for every module.


.. note:: Previously, we used ``vcrpy`` and ``pytest-vcr`` packages to manage
          recorded tapes for interaction with Mailman Core. That was replaced
          with ``pytest-services`` plugin, which instead start Core for every
          test.


.. _`tox`: https://testrun.org/tox/latest/
.. _`pytest`: https://docs.pytest.org/en/latest/
