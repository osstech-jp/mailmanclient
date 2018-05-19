# Copyright (C) 2010-2018 by the Free Software Foundation, Inc.
#
# This file is part of mailmanclient.
#
# mailmanclient is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, version 3 of the License.
#
# mailmanclient is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public
# License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with mailmanclient.  If not, see <http://www.gnu.org/licenses/>.

"""Client code."""

from __future__ import absolute_import, unicode_literals

import warnings
from operator import itemgetter

from mailmanclient.constants import (MISSING)
from mailmanclient.restobjects.address import Address
from mailmanclient.restobjects.ban import Bans, BannedAddress
from mailmanclient.restobjects.configuration import Configuration
from mailmanclient.restobjects.domain import Domain
from mailmanclient.restobjects.mailinglist import MailingList
from mailmanclient.restobjects.member import Member
from mailmanclient.restobjects.preferences import Preferences
from mailmanclient.restobjects.queue import Queue
from mailmanclient.restobjects.styles import Styles
from mailmanclient.restobjects.user import User
from mailmanclient.restobjects.templates import Template, TemplateList
from mailmanclient.restbase.connection import Connection
from mailmanclient.restbase.page import Page

__metaclass__ = type
__all__ = [
    'Client'
]


#
# --- The following classes are part of the API
#

class Client:
    """Access the Mailman REST API root.

    :param baseurl: The base url to access the Mailman 3 REST API.
    :param name: The Basic Auth user name.  If given, the `password` must
        also be given.
    :param password: The Basic Auth password.  If given the `name` must
        also be given.
    """

    def __init__(self, baseurl, name=None, password=None):
        """Initialize client access to the REST API.
        """
        self._connection = Connection(baseurl, name, password)

    def __repr__(self):
        return '<Client ({0.name}:{0.password}) {0.baseurl}>'.format(
            self._connection)

    @property
    def system(self):
        """
        Get the basic system information.
        """
        return self._connection.call('system/versions')[1]

    @property
    def preferences(self):
        """
        Get all default system Preferences.
        """
        return Preferences(self._connection, 'system/preferences')

    @property
    def configuration(self):
        """
        Get the system configuration.
        """
        response, content = self._connection.call('system/configuration')
        return {section: Configuration(
            self._connection, section) for section in content['sections']}

    @property
    def pipelines(self):
        """
        Get a list of all Pipelines.
        """
        response, content = self._connection.call('system/pipelines')
        return content

    @property
    def chains(self):
        """
        Get a list of all the Chains.
        """
        response, content = self._connection.call('system/chains')
        return content

    @property
    def queues(self):
        """
        Get a list of all Queues.
        """
        response, content = self._connection.call('queues')
        queues = {}
        for entry in content['entries']:
            queues[entry['name']] = Queue(
                self._connection, entry['self_link'], entry)
        return queues

    @property
    def styles(self):
        return Styles(self._connection, 'lists/styles')

    @property
    def lists(self):
        """
        Get a list of all MailingLists.
        """
        return self.get_lists()

    def get_lists(self, advertised=None):
        """Get a list of all the MailingLists.

        :param advertised: If marked True, returns all MailingLists including
                           the ones that aren't advertised.
        :type advertised: Bool
        """
        url = 'lists'
        if advertised:
            url += '?advertised=true'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        return [MailingList(self._connection, entry['self_link'], entry)
                for entry in content['entries']]

    def get_list_page(self, count=50, page=1, advertised=None):
        """
        Get a list of all MailingList with pagination.

        :param count: Number of entries per-page (defaults to 50).
        :param page: The page number to return (defaults to 1).
        :param advertised: If marked True, returns all MailingLists including
                           the ones that aren't advertised.
        """
        url = 'lists'
        if advertised:
            url += '?advertised=true'
        return Page(self._connection, url, MailingList, count, page)

    @property
    def domains(self):
        """
        Get a list of all Domains.
        """
        response, content = self._connection.call('domains')
        if 'entries' not in content:
            return []
        return [Domain(self._connection, entry['self_link'])
                for entry in sorted(content['entries'],
                                    key=itemgetter('mail_host'))]

    @property
    def members(self):
        """
        Get a list of all the Members.
        """
        response, content = self._connection.call('members')
        if 'entries' not in content:
            return []
        return [Member(self._connection, entry['self_link'], entry)
                for entry in content['entries']]

    def get_member(self, fqdn_listname, subscriber_address):
        """
        Get the Member object for a given MailingList and Subsciber's Email
        Address.

        :param fqdn_listname: Fully qualified address for the MailingList.
        :param subscriber_address: Email Address for the subscriber.
        """
        return self.get_list(fqdn_listname).get_member(subscriber_address)

    def get_member_page(self, count=50, page=1):
        return Page(self._connection, 'members', Member, count, page)

    @property
    def users(self):
        """
        Get all the users.
        """
        response, content = self._connection.call('users')
        if 'entries' not in content:
            return []
        return [User(self._connection, entry['self_link'], entry)
                for entry in sorted(content['entries'],
                                    key=itemgetter('self_link'))]

    def get_user_page(self, count=50, page=1):
        """
        Get all the users with pagination.

        :param count: Number of entries per-page (defaults to 50).
        :param page: The page number to return (defaults to 1).
        """
        return Page(self._connection, 'users', User, count, page)

    def create_domain(self, mail_host, base_url=MISSING,
                      description=None, owner=None, alias_domain=None):
        """
        Create a new Domain.

        :param mail_host: The Mail host for the new domain. If you want
                          "foo@bar.com" as the address for your MailingList,
                          use "bar.com" here.
        :param description: A brief description for this Domain.
        :param owner: Email address for the owner of this list.
        :param alias_domain: Alias domain.
        """
        if base_url is not MISSING:
            warnings.warn(
                'The `base_url` parameter in the `create_domain()` method is '
                'deprecated. It is not used any more and will be removed in '
                'the future.', DeprecationWarning, stacklevel=2)
        data = dict(mail_host=mail_host)
        if description is not None:
            data['description'] = description
        if owner is not None:
            data['owner'] = owner
        if alias_domain is not None:
            data['alias_domain'] = alias_domain
        response, content = self._connection.call('domains', data)
        return Domain(self._connection, response['location'])

    def delete_domain(self, mail_host):
        """
        Delete a Domain.

        :param mail_host: The Mail host for the domain you want to delete.
        """
        response, content = self._connection.call(
            'domains/{0}'.format(mail_host), None, 'DELETE')

    def get_domain(self, mail_host, web_host=MISSING):
        """
        Get Domain by its mail_host.
        """
        if web_host is not MISSING:
            warnings.warn(
                'The `web_host` parameter in the `get_domain()` method is '
                'deprecated. It is not used any more and will be removed in '
                'the future.', DeprecationWarning, stacklevel=2)
        response, content = self._connection.call(
            'domains/{0}'.format(mail_host))
        return Domain(self._connection, content['self_link'])

    def create_user(self, email, password, display_name=''):
        """
        Create a new User.

        :param email: Email address for the new user.
        :param password: Password for the new user.
        :param display_name: An optional name for the new user.
        """
        response, content = self._connection.call(
            'users', dict(email=email,
                          password=password,
                          display_name=display_name))
        return User(self._connection, response['location'])

    def get_user(self, address):
        """
        Given an Email Address, return the User it belongs to.

        :param address: Email Address of the User.
        """
        response, content = self._connection.call(
            'users/{0}'.format(address))
        return User(self._connection, content['self_link'], content)

    def get_address(self, address):
        """
        Given an Email Address, return the Address object.

        :param address: Email address.
        """
        response, content = self._connection.call(
            'addresses/{0}'.format(address))
        return Address(self._connection, content['self_link'], content)

    def get_list(self, fqdn_listname):
        """
        Get a MailingList object.

        :param fqdn_listname: Fully qualified name of the MailingList.
        """
        response, content = self._connection.call(
            'lists/{0}'.format(fqdn_listname))
        return MailingList(self._connection, content['self_link'], content)

    def delete_list(self, fqdn_listname):
        """
        Delete a MailingList.

        :param fqdn_listname: Fully qualified name of the MailingList.
        """
        response, content = self._connection.call(
            'lists/{0}'.format(fqdn_listname), None, 'DELETE')

    @property
    def bans(self):
        """
        Get a list of all the bans.
        """
        return Bans(self._connection, 'bans', mlist=None)

    def get_bans_page(self, count=50, page=1):
        """
        Get a list of all the bans with pagination.

        :param count: Number of entries per-page (defaults to 50).
        :param page: The page number to return (defaults to 1).
        """
        return Page(self._connection, 'bans', BannedAddress, count, page)

    @property
    def templates(self):
        """Get all site-context templates.
        """
        return TemplateList(self._connection, 'uris')

    def get_templates_page(self, count=25, page=1):
        """Get paginated site-context templates.
        """
        return Page(self._connection, 'uris', Template, count, page)

    def set_template(self, template_name, url, username=None, password=None):
        """Set template in site-context.
        """
        data = {template_name: url}
        if username is not None and password is not None:
            data['username'] = username
            data['password'] = password
        return self._connection.call('uris', data, 'PATCH')[1]

    def find_lists(self, subscriber, role=None, count=50, page=1):
        """
        Given a subscriber and a role, return all the list they are subscribed
        to with given role.

        If no role is specified all the related mailing lists are returned
        without duplicates, even though there can potentially be multiple
        memberships of a user in a single mailing list.

        :param subscriber: The address of the subscriber.
        :type subscriber: str
        :param role: owner, moderator or subscriber
        :type role: str
        """
        url = 'lists/find'
        data = dict(subscriber=subscriber, count=count, page=page)
        if role is not None:
            data['role'] = role
        response, content = self._connection.call(url, data)
        if 'entries' not in content:
            return []
        return [MailingList(self._connection, entry['self_link'], entry)
                for entry in content['entries']]
