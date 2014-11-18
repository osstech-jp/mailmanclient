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

"""Test tools."""

from __future__ import absolute_import, unicode_literals, print_function

from urllib2 import HTTPError
from urlparse import urljoin

from webtest import TestApp
import mailmanclient

__metaclass__ = type
__all__ = [
    "FakeMailmanClient",
    ]



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

    def call(self, path, data=None, method=None):
        self.called_paths.append(path)
        if method is None:
            if data is None:
                method = 'GET'
            else:
                method = 'POST'
        method_fn = getattr(self.app, method.lower())
        if self.basic_auth:
            self.app.authorization = ('Basic', (self.name, self.password))
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
            raise MailmanConnectionError('Could not connect to Mailman API')



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
