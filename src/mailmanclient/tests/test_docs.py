# Copyright (C) 2010-2014 by The Free Software Foundation, Inc.
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

from __future__ import absolute_import, unicode_literals, print_function

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
from textwrap import dedent

from mock import patch
# pylint: disable-msg=F0401
from pkg_resources import (
    resource_filename, resource_exists, resource_listdir, cleanup_resources)
from zope.component import getUtility

from mailman.config import config
from mailman.testing.layers import ConfigLayer
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.usermanager import IUserManager
from mailman.core.chains import process
from mailman.testing.helpers import specialized_message_from_string
from mailmanclient.tests.utils import FakeMailmanClient


COMMASPACE = ', '
DOT = '.'
DOCTEST_FLAGS = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_NDIFF)



def dump(results):
    if results is None:
        print(None)
        return
    for key in sorted(results):
        if key == 'entries':
            for i, entry in enumerate(results[key]):
                # entry is a dictionary.
                print('entry %d:' % i)
                for entry_key in sorted(entry):
                    print('    {0}: {1}'.format(entry_key, entry[entry_key]))
        else:
            print('{0}: {1}'.format(key, results[key]))



def stop():
    """Call into pdb.set_trace()"""
    # Do the import here so that you get the wacky special hacked pdb instead
    # of Python's normal pdb.
    import pdb
    pdb.set_trace()



def inject_message(fqdn_listname, msg):
    mlist = getUtility(IListManager).get(fqdn_listname)
    user_manager = getUtility(IUserManager)
    msg = specialized_message_from_string(msg)
    for sender in msg.senders:
        if user_manager.get_address(sender) is None:
            user_manager.create_address(sender)
    process(mlist, msg, {})



def setup(testobj):
    testobj.globs['stop'] = stop
    testobj.globs['dump'] = dump
    testobj.globs['inject_message'] = inject_message
    ConfigLayer.setUp()
    # In unit tests, passwords aren't encrypted. Don't show this in the doctests
    passlib_cfg = os.path.join(config.VAR_DIR, 'passlib.cfg')
    with open(passlib_cfg, 'w') as fp:
        print(dedent("""
            [passlib]
            schemes = sha512_crypt
            """), file=fp)
    conf_hash_pw = dedent("""
    [passwords]
    configuration: {}
    """.format(passlib_cfg))
    config.push('conf_hash_pw', conf_hash_pw)
    # Use the FakeMailmanClient
    testobj.patcher = patch("mailmanclient.Client", FakeMailmanClient)
    fmc = testobj.patcher.start()



def teardown(testobj):
    """Test teardown."""
    testobj.patcher.stop()
    config.pop('conf_hash_pw')
    config.create_paths = False # or ConfigLayer.tearDown will create them
    ConfigLayer.tearDown()



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
