# Copyright (C) 2010 by the Free Software Foundation, Inc.
#
# This file is part of mailman.client.
#
# mailman.client is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, version 3 of the License.
#
# mailman.client is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with mailman.client.  If not, see <http://www.gnu.org/licenses/>.

"""Client code."""

from __future__ import absolute_import, unicode_literals

__metaclass__ = type
__all__ = [
    'Client',
    ]


import json

from base64 import b64encode
from httplib2 import Http
from operator import itemgetter
from urllib import urlencode
from urllib2 import HTTPError
from urlparse import urljoin


from mailman.client import __version__



class _Connection:
    """A connection to the REST client."""

    def __init__(self, baseurl, name=None, password=None):
        """Initialize a connection to the REST API.

        :param baseurl: The base url to access the Mailman 3 REST API.
        :param name: The Basic Auth user name.  If given, the `password` must
            also be given.
        :param password: The Basic Auth password.  If given the `name` must
            also be given.
        """
        if baseurl[-1] != '/':
            baseurl += '/'
        self.baseurl = baseurl
        self.name = name
        self.password = password
        if name is not None and password is None:
            raise TypeError('`password` is required when `name` is given')
        if name is None and password is not None:
            raise TypeError('`name` is required when `password` is given')
        if name is None:
            self.basic_auth = None
        else:
            auth = '{0}:{1}'.format(name, password)
            self.basic_auth = b64encode(auth)

    def call(self, path, data=None, method=None):
        """Make a call to the Mailman REST API.

        :param path: The url path to the resource.
        :type path: str
        :param data: Data to send, implies POST (default) or PUT.
        :type data: dict
        :param method: The HTTP method to call.  Defaults to GET when `data`
            is None or POST if `data` is given.
        :type method: str
        :return: The response content, which will be None, a dictionary, or a
            list depending on the actual JSON type returned.
        :rtype: None, list, dict
        :raises HTTPError: when a non-2xx status code is returned.
        """
        headers = {
            'User-Agent': 'GNU Mailman REST client v{0}'.format(__version__),
            }
        if data is not None:
            data = urlencode(data, doseq=True)
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        if method is None:
            if data is None:
                method = 'GET'
            else:
                method = 'POST'
        method = method.upper()
        if self.basic_auth:
            headers['Authorization'] = 'Basic ' + self.basic_auth
        url = urljoin(self.baseurl, path)
        response, content = Http().request(url, method, data, headers)
        # If we did not get a 2xx status code, make this look like a urllib2
        # exception, for backward compatibility.
        if response.status // 100 != 2:
            raise HTTPError(url, response.status, content, response, None)
        if len(content) == 0:
            return response, None
        # XXX Work around for http://bugs.python.org/issue10038
        content = unicode(content)
        return response, json.loads(content)



class Client:
    """Access the Mailman REST API root."""

    def __init__(self, baseurl, name=None, password=None):
        """Initialize client access to the REST API.

        :param baseurl: The base url to access the Mailman 3 REST API.
        :param name: The Basic Auth user name.  If given, the `password` must
            also be given.
        :param password: The Basic Auth password.  If given the `name` must
            also be given.
        """
        self._connection = _Connection(baseurl, name, password)

    def __repr__(self):
        return '<Client ({0.name}:{0.password}) {0.baseurl}>'.format(
            self._connection)

    @property
    def system(self):
        return self._connection.call('system')[1]

    @property
    def lists(self):
        response, content = self._connection.call('lists')
        if 'entries' not in content:
            return []
        return sorted(content['entries'], key=itemgetter('fqdn_listname'))

    @property
    def domains(self):
        response, content = self._connection.call('domains')
        if 'entries' not in content:
            return []
        return sorted(content['entries'], key=itemgetter('url_host'))

    def create_domain(self, email_host, base_url=None,
                      description=None, contact_address=None):
        data = dict(email_host=email_host)
        if base_url is not None:
            data['base_url'] = base_url
        if description is not None:
            data['description'] = description
        if contact_address is not None:
            data['contact_address'] = contact_address
        response, content = self._connection.call('domains', data)
        return _Domain(self._connection, response['location'])

    def get_domain(self, email_host):
        response, content = self._connection.call(
            'domains/{0}'.format(email_host))
        return _Domain(self._connection, content['self_link'])



class _Domain:
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        response, content = self._connection.call(url)
        self.base_url = content['base_url']
        self.contact_address = content['contact_address']
        self.description = content['description']
        self.email_host = content['email_host']
        self.url_host = content['url_host']

    def __repr__(self):
        return '<Domain "{0}">'.format(self.email_host)
