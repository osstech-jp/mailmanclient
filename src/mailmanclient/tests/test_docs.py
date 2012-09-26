# Copyright (C) 2010 by The Free Software Foundation, Inc.
#
# This file is part of mailman.client.
#
# mailman.client is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# mailman.client is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with mailman.client.  If not, see <http://www.gnu.org/licenses/>.

"""Test harness for doctests."""

from __future__ import absolute_import, unicode_literals

__metaclass__ = type
__all__ = [
    'additional_tests',
    ]


import os
import time
import atexit
import shutil
import doctest
import tempfile
import unittest
import subprocess

# pylint: disable-msg=F0401
from pkg_resources import (
    resource_filename, resource_exists, resource_listdir, cleanup_resources)


COMMASPACE = ', '
DOT = '.'
DOCTEST_FLAGS = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_NDIFF)



def dump(results):
    if results is None:
        print None
        return
    for key in sorted(results):
        if key == 'entries':
            for i, entry in enumerate(results[key]):
                # entry is a dictionary.
                print 'entry %d:' % i
                for entry_key in sorted(entry):
                    print '    {0}: {1}'.format(entry_key, entry[entry_key])
        else:
            print '{0}: {1}'.format(key, results[key])



def stop():
    """Call into pdb.set_trace()"""
    # Do the import here so that you get the wacky special hacked pdb instead
    # of Python's normal pdb.
    import pdb
    pdb.set_trace()



def setup(testobj):
    """Test setup."""
    # Create a unique database for the running version of Mailman, then start
    # it up.  It should not yet be running.  This environment variable must be
    # set to find the installation of Mailman we can run.  Yes, this should be
    # fixed.
    testobj._bindir = os.environ.get('MAILMAN_TEST_BINDIR')
    if testobj._bindir is None:
        raise RuntimeError('Must set $MAILMAN_TEST_BINDIR to run tests')
    vardir = testobj._vardir = tempfile.mkdtemp()
    cfgfile = testobj._cfgfile = os.path.join(vardir, 'client_test.cfg')
    with open(cfgfile, 'w') as fp:
        print >> fp, """\
[mailman]
layout: tmpdir
[paths.tmpdir]
var_dir: {vardir}
log_dir: /tmp/mmclient/logs
[runner.archive]
start: no
[runner.bounces]
start: no
[runner.command]
start: no
[runner.in]
start: no
[runner.lmtp]
start: no
[runner.news]
start: no
[runner.out]
start: no
[runner.pipeline]
start: no
[runner.retry]
start: no
[runner.virgin]
start: no
[runner.digest]
start: no
""".format(vardir=vardir)
    mailman = os.path.join(testobj._bindir, 'mailman')
    subprocess.call([mailman, '-C', cfgfile, 'start', '-q'])
    time.sleep(3)
    # Make sure future statements in our doctests match the Python code.  When
    # run with 2to3, the future import gets removed and these names are not
    # defined.
    try:
        testobj.globs['absolute_import'] = absolute_import
        testobj.globs['unicode_literals'] = unicode_literals
    except NameError:
        pass
    testobj.globs['stop'] = stop
    testobj.globs['dump'] = dump


def teardown(testobj):
    """Test teardown."""
    mailman = os.path.join(testobj._bindir, 'mailman')
    subprocess.call([mailman, '-C', testobj._cfgfile, 'stop', '-q'])
    shutil.rmtree(testobj._vardir)
    time.sleep(3)



def additional_tests():
    "Run the doc tests (README.txt and docs/*, if any exist)"
    doctest_files = []
    if resource_exists('mailmanclient', 'docs'):
        for name in resource_listdir('mailmanclient', 'docs'):
            if name.endswith('.txt'):
                doctest_files.append(
                    os.path.abspath(
                        resource_filename('mailmanclient', 'docs/%s' % name)))
    kwargs = dict(module_relative=False,
                  optionflags=DOCTEST_FLAGS,
                  setUp=setup, tearDown=teardown,
                  )
    atexit.register(cleanup_resources)
    return unittest.TestSuite((
        doctest.DocFileSuite(*doctest_files, **kwargs)))
