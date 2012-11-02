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
    'MailmanConnectionError',
    ]


import re
import json

from base64 import b64encode
from httplib2 import Http
from operator import itemgetter
from urllib import urlencode
from urllib2 import HTTPError
from urlparse import urljoin


from mailmanclient import __version__



def _member_key(member_dict):
    """Return the keys for sorting a member.

    :param member_dict: The JSON dictionary for a member.
    :return: 2-tuple of (fqdn_listname, address)
    """
    return (member_dict['list_id'], member_dict['address'])


class MailmanConnectionError(Exception):
    """Custom Exception to catch connection errors."""
    pass


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
        try:
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
        except HTTPError:
            raise
        except IOError:
            raise MailmanConnectionError('Could not connect to Mailman API')


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
    def preferences(self):
        return self._connection.call('system/preferences')[1]

    @property
    def lists(self):
        response, content = self._connection.call('lists')
        if 'entries' not in content:
            return []
        return [_List(self._connection, entry['self_link'])
                for entry in sorted (content['entries'],
                                     key=itemgetter('fqdn_listname'))]

    @property
    def domains(self):
        response, content = self._connection.call('domains')
        if 'entries' not in content:
            return []
        return [_Domain(self._connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('url_host'))]

    @property
    def members(self):
        response, content = self._connection.call('members')
        if 'entries' not in content:
            return []
        return [_Member(self._connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=_member_key)]

    @property
    def users(self):
        response, content = self._connection.call('users')
        if 'entries' not in content:
            return []
        return [_User(self._connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('self_link'))]

    def create_domain(self, mail_host, base_url=None,
                      description=None, contact_address=None):
        data = dict(mail_host=mail_host)
        if base_url is not None:
            data['base_url'] = base_url
        if description is not None:
            data['description'] = description
        if contact_address is not None:
            data['contact_address'] = contact_address
        response, content = self._connection.call('domains', data)
        return _Domain(self._connection, response['location'])

    def delete_domain(self, mail_host):
        response, content = self._connection.call('domains/{0}'
                                                  .format(mail_host),
                                                  None, 'DELETE')

    def get_domain(self, mail_host=None, web_host=None):
        """Get domain by its mail_host or its web_host."""
        if mail_host is not None:
            response, content = self._connection.call(
                'domains/{0}'.format(mail_host))
            return _Domain(self._connection, content['self_link'])
        elif web_host is not None:
            for domain in self.domains:
                # note: `base_url` property will be renamed to `web_host`
                # in Mailman3Alpha8
                if domain.base_url == web_host:
                    return domain
                    break
            else:
                return None

    def create_user(self, email, password, display_name=''):
        response, content = self._connection.call(
            'users', dict(email=email, password=password,
                          display_name=display_name))
        return _User(self._connection, response['location'])

    def get_user(self, address):
        response, content = self._connection.call(
            'users/{0}'.format(address))
        return _User(self._connection, content['self_link'])

    def get_address(self, address):
        response, content = self._connection.call(
            'addresses/{0}'.format(address))
        return _Address(self._connection, content)

    def get_list(self, fqdn_listname):
        response, content = self._connection.call(
            'lists/{0}'.format(fqdn_listname))
        return _List(self._connection, content['self_link'])

    def delete_list(self, fqdn_listname):
        response, content = self._connection.call(
            'lists/{0}'.format(fqdn_listname), None, 'DELETE')


class _Domain:
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        self._info = None

    def __repr__(self):
        return '<Domain "{0}">'.format(self.mail_host)

    def _get_info(self):
        if self._info is None:
            response, content = self._connection.call(self._url)
            self._info = content

    # note: `base_url` property will be renamed to `web_host`
    # in Mailman3Alpha8
    @property
    def base_url(self):
        self._get_info()
        return self._info['base_url']

    @property
    def contact_address(self):
        self._get_info()
        return self._info['contact_address']

    @property
    def description(self):
        self._get_info()
        return self._info['description']

    @property
    def mail_host(self):
        self._get_info()
        return self._info['mail_host']

    @property
    def url_host(self):
        self._get_info()
        return self._info['url_host']

    @property
    def lists(self):
        response, content = self._connection.call(
            'domains/{0}/lists'.format(self.mail_host))
        if 'entries' not in content:
            return []
        return [_List(self._connection, entry['self_link'])
                for entry in sorted (content['entries'],
                                     key=itemgetter('fqdn_listname'))]

    def create_list(self, list_name):
        fqdn_listname = '{0}@{1}'.format(list_name, self.mail_host)
        response, content = self._connection.call(
            'lists', dict(fqdn_listname=fqdn_listname))
        return _List(self._connection, response['location'])


class _List:
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        self._info = None

    def __repr__(self):
        return '<List "{0}">'.format(self.fqdn_listname)

    def _get_info(self):
        if self._info is None:
            response, content = self._connection.call(self._url)
            self._info = content

    @property
    def owners(self):
        url = self._url + '/roster/owner'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        else:
            return [item['address'] for item in content['entries']]
        
    @property
    def moderators(self):
        url = self._url + '/roster/moderator'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        else:
            return [item['address'] for item in content['entries']]

    @property
    def fqdn_listname(self):
        self._get_info()
        return self._info['fqdn_listname']

    @property
    def mail_host(self):
        self._get_info()
        return self._info['mail_host']

    @property
    def list_id(self):
        self._get_info()
        return self._info['list_id']

    @property
    def list_name(self):
        self._get_info()
        return self._info['list_name']

    @property
    def display_name(self):
        self._get_info()
        return self._info.get('display_name')

    @property
    def members(self):
        url = 'lists/{0}/roster/member'.format(self.fqdn_listname)
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        return [_Member(self._connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('address'))]

    @property
    def settings(self):
        return _Settings(self._connection,
            'lists/{0}/config'.format(self.fqdn_listname))

    @property
    def held(self):
        """Return a list of dicts with held message information.
        """
        response, content = self._connection.call(
            'lists/{0}/held'.format(self.fqdn_listname), None, 'GET')
        if 'entries' not in content:
            return []
        else:
            entries = []
            for entry in content['entries']:
                msg = dict(subject=entry['data']['_mod_subject'],
                           fqdn_listname=entry['data']['_mod_fqdn_listname'],
                           hold_date=entry['data']['_mod_hold_date'],
                           reason=entry['data']['_mod_reason'],
                           sender=entry['data']['_mod_sender'],
                           id=entry['id'])
                entries.append(msg)
        return entries

    def add_owner(self, address):
        self.add_role('owner', address)

    def add_moderator(self, address):
        self.add_role('moderator', address)

    def add_role(self, role, address):
        data = dict(list_id=self.list_id,
                    subscriber=address,
                    role=role)
        self._connection.call('members', data)

    def remove_owner(self, address):
        self.remove_role('owner', address)

    def remove_moderator(self, address):
        self.remove_role('moderator', address)

    def remove_role(self, role, address):
        url = 'lists/%s/%s/%s' % (self.fqdn_listname, role, address)
        self._connection.call(url, method='DELETE')
        
    def moderate_message(self, request_id, action):
        """Moderate a held message.
        
        :param request_id: Id of the held message.
        :type request_id: Int.
        :param action: Action to perform on held message.
        :type action: String.
        """
        path = 'lists/{0}/held/{1}'.format(self.fqdn_listname, 
                                          str(request_id))
        response, content = self._connection.call(path, dict(action=action),
                                                  'POST')
        return response

    def discard_message(self, request_id):
        """Shortcut for moderate_message.
        """
        return self.moderate_message(request_id, 'discard')

    def reject_message(self, request_id):
        """Shortcut for moderate_message.
        """
        return self.moderate_message(request_id, 'reject')

    def defer_message(self, request_id):
        """Shortcut for moderate_message.
        """
        return self.moderate_message(request_id, 'defer')

    def accept_message(self, request_id):
        """Shortcut for moderate_message.
        """
        return self.moderate_message(request_id, 'accept')

    def get_member(self, address):
        """Get a membership.

        :param address: The email address of the member for this list.
        :return: A member proxy object.
        """
        # In order to get the member object we need to
        # iterate over the existing member list
        for member in self.members:
            if member.address == address:
                return member
                break
        else:
            raise ValueError('%s is not a member address of %s' %
                             (address, self.fqdn_listname))

    def subscribe(self, address, display_name=None):
        """Subscribe an email address to a mailing list.

        :param address: Email address to subscribe to the list.
        :type address: str
        :param display_name: The real name of the new member.
        :type display_name: str
        :return: A member proxy object.
        """
        data = dict(
            list_id=self.list_id,
            subscriber=address,
            display_name=display_name,
            )
        response, content = self._connection.call('members', data)
        return _Member(self._connection, response['location'])

    def unsubscribe(self, address):
        """Unsubscribe an email address from a mailing list.

        :param address: The address to unsubscribe.
        """
        # In order to get the member object we need to
        # iterate over the existing member list

        for member in self.members:
            if member.address == address:
                self._connection.call(member.self_link, method='DELETE')
                break
        else:
            raise ValueError('%s is not a member address of %s' %
                             (address, self.fqdn_listname))


    def delete(self):
        response, content = self._connection.call(
            'lists/{0}'.format(self.fqdn_listname), None, 'DELETE')


class _Member:
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        self._info = None

    def __repr__(self):
        return '<Member "{0}" on "{1}">'.format(
            self.address, self.list_id)

    def _get_info(self):
        if self._info is None:
            response, content = self._connection.call(self._url)
            self._info = content
        
    @property
    def list_id(self):
        self._get_info()
        return self._info['list_id']

    @property
    def role(self):
        self._get_info()
        return self._info['role']
        
    @property
    def address(self):
        self._get_info()
        return self._info['address']

    @property
    def self_link(self):
        self._get_info()
        return self._info['self_link']

    @property
    def role(self):
        self._get_info()
        return self._info['role']

    @property
    def user(self):
        self._get_info()
        return self._info['user']

    def unsubscribe(self):
        """Unsubscribe the member from a mailing list.

        :param self_link: The REST resource to delete
        """
        self._connection.call(self.self_link, method='DELETE')


class _User:
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        self._info = None
        self._addresses = None
        self._preferences = None
        self._cleartext_password = None

    def __repr__(self):
        return '<User "{0}" ({1})>'.format(
            self.display_name, self.user_id)

    def _get_info(self):
        if self._info is None:
            response, content = self._connection.call(self._url)
            self._info = content

    @property
    def addresses(self):
        return _Addresses(self._connection, self.user_id)
    
    @property
    def display_name(self):
        self._get_info()
        return self._info.get('display_name', None)

    @display_name.setter
    def display_name(self, value):
        self._info['display_name'] = value

    @property
    def password(self):
        self._get_info()
        return self._info.get('password', None)

    @password.setter
    def password(self, value):
        self._cleartext_password = value

    @property
    def user_id(self):
        self._get_info()
        return self._info['user_id']

    @property
    def created_on(self):
        self._get_info()
        return self._info['created_on']

    @property
    def self_link(self):
        self._get_info()
        return self._info['self_link']

    @property
    def preferences(self):
        return _Preferences(self._connection, self.address)

    def save(self):
        data = {'display_name': self.display_name}
        if self._cleartext_password is not None:
            data['cleartext_password'] = self._cleartext_password
        self.cleartext_password = None
        response, content = self._connection.call(self._url,
                                                  data, method='PATCH')
        self._info = None

    def delete(self):
        response, content = self._connection.call(self._url, method='DELETE')
        

class _Addresses:
    def __init__(self, connection, user_id):
        self._connection = connection
        self._user_id = user_id
        self._addresses = None
        self._get_addresses()

    def _get_addresses(self):
        if self._addresses is None:
            response, content = self._connection.call('users/{0}/addresses'
                                                      .format(self._user_id))
            if 'entries' not in content:
                self._addresses = []
            self._addresses = content['entries']

    def __iter__(self):
        for address in self._addresses:
            yield _Address(self._connection, address)

class _Preferences:
    def __init__(self, connection, address):
        self._connection = connection
        self._address = address
        self._preferences = None
        self._get_preferences()

    def _get_preferences(self):
        if self._preferences is None:
            response, content = self._connection.call('addresses/{0}/preferences'.format(self._address))
            if 'entries' not in content:
                self._preferences= []
            self._preferences = content['entries']

    def __iter__(self):
        for preference in self._preferences:
            yield _Preference(self._connection, preference)

class _Address:
    def __init__(self, connection, address):
        self._connection = connection
        self._address = address
        self._url = address['self_link']
        self._info = None

    def __repr__(self):
        return self._address['email']

    def _get_info(self):
        if self._info is None:
            response, content = self._connection.call(self._url)
            self._info = content

    @property
    def display_name(self):
        self._get_info()
        return self._info.get('display_name')

    @property
    def registered_on(self):
        self._get_info()
        return self._info.get('registered_on')

    @property
    def verified_on(self):
        self._get_info()
        return self._info.get('verified_on')

    def verify(self):
        self._connection.call('addresses/{0}/verify'
                              .format(self._address['email']), method='POST')
        self._info = None

    def unverify(self):
        self._connection.call('addresses/{0}/unverify'
                              .format(self._address['email']), method='POST')
        self._info = None


LIST_READ_ONLY_ATTRS = ('bounces_address', 'created_at', 'digest_last_sent_at',
                        'fqdn_listname', 'http_etag', 'mail_host',
                        'join_address', 'last_post_at', 'leave_address',
                        'list_id', 'list_name', 'next_digest_number',
                        'no_reply_address', 'owner_address', 'post_id',
                        'posting_address', 'request_address', 'scheme',
                        'volume', 'web_host',)


class _Settings():
    def __init__(self, connection, url):
        self._connection = connection
        self._url = url
        self._info = None
        self._get_info()

    def __repr__(self):
        return repr(self._info)

    def _get_info(self):
        if self._info is None:
            response, content = self._connection.call(self._url)
            self._info = content

    def __iter__(self):
        for key in self._info.keys():
            yield key

    def __getitem__(self, key):
        return self._info[key]

    def __setitem__(self, key, value):
        self._info[key] = value

    def __len__(self):
        return len(self._info)

    def get(self, key, default=None):
        try:
            return self._info[key]
        except KeyError:
            return default

    def save(self):
        data = {}
        for attribute, value in self._info.items():
            if attribute not in LIST_READ_ONLY_ATTRS:
                data[attribute] = value
        response, content = self._connection.call(self._url, data, 'PATCH')
