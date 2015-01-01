# Copyright (C) 2010-2015 by the Free Software Foundation, Inc.
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

"""Test tools."""

from __future__ import absolute_import, unicode_literals, print_function

import os
from urllib2 import HTTPError
from urlparse import urljoin

from zope.component import getUtility
from webtest import TestApp

from mailman.config import config
from mailman.core.chains import process
from mailman.interfaces.listmanager import IListManager
from mailman.interfaces.usermanager import IUserManager
from mailman.testing.helpers import specialized_message_from_string
from mailman.testing.layers import ConfigLayer
import mailmanclient

__metaclass__ = type
__all__ = [
    "inject_message",
    "FakeMailmanClient",
    ]



def inject_message(fqdn_listname, msg):
    mlist = getUtility(IListManager).get(fqdn_listname)
    user_manager = getUtility(IUserManager)
    msg = specialized_message_from_string(msg)
    for sender in msg.senders:
        if user_manager.get_address(sender) is None:
            user_manager.create_address(sender)
    process(mlist, msg, {})


#
# Mocking mailman client
#


class FakeConnection(mailmanclient._client._Connection):
    """
    Looks for information inside a dict instead of making HTTP requests.
    Also, logs the called URLs as called_paths.
    Very incomplete at the moment.
    """

    def __init__(self, baseurl, name=None, password=None):
        super(FakeConnection, self).__init__(baseurl, name, password)
        self.called_paths = []
        from mailman.rest.wsgiapp import make_application
        self.app = TestApp(make_application())
        if self.basic_auth:
            self.app.authorization = ('Basic', (self.name, self.password))
        super(FakeConnection, self).__init__(baseurl, name, password)

    def call(self, path, data=None, method=None):
        self.called_paths.append(
                { "path": path, "data": data, "method": method })
        if method is None:
            if data is None:
                method = 'GET'
            else:
                method = 'POST'
        method_fn = getattr(self.app, method.lower())
        url = urljoin(self.baseurl, path)
        try:
            kw = {"expect_errors": True}
            if data:
                kw["params"] = data
            response = method_fn(url, **kw)
            headers = response.headers
            headers["status"] = response.status_int
            content = unicode(response.body)
            # If we did not get a 2xx status code, make this look like a
            # urllib2 exception, for backward compatibility.
            if response.status_int // 100 != 2:
                raise HTTPError(url, response.status_int, content, headers, None)
            if len(content) == 0:
                return headers, None
            # XXX Work around for http://bugs.python.org/issue10038
            return headers, response.json
        except HTTPError:
            raise
        except IOError:
            raise mailmanclient.MailmanConnectionError(
                'Could not connect to Mailman API')



class FakeMailmanClient(mailmanclient.Client):
    """
    Subclass of mailmanclient.Client to instantiate a FakeConnection object
    instead of the real connection.
    """

    def __init__(self, baseurl, name=None, password=None):
        self._connection = FakeConnection(baseurl, name, password)

    @property
    def called_paths(self):
        return self._connection.called_paths

    @classmethod
    def setUp(self):
        ConfigLayer.setUp()

    @classmethod
    def tearDown(self):
        config.create_paths = False # or ConfigLayer.tearDown will create them
        ConfigLayer.testTearDown()
        ConfigLayer.tearDown()
        reset_mailman_config()

def reset_mailman_config():
    # This is necessary because ConfigLayer.setup/tearDown was designed to be
    # run only once for the whole test suite, and thus does not reset
    # everything afterwards
    for prop in ("switchboards", "rules", "chains", "handlers",
                 "pipelines", "commands"):
        getattr(config, prop).clear()
    from mailman.model.user import uid_factory
    uid_factory._lockobj = None
    from mailman.model.member import uid_factory
    uid_factory._lockobj = None
