# Copyright (C) 2010-2019 by the Free Software Foundation, Inc.
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
import warnings
from operator import itemgetter
from urllib.error import HTTPError
from urllib.parse import urlencode, quote_plus

from mailmanclient.restobjects.header_match import HeaderMatches
from mailmanclient.restobjects.archivers import ListArchivers
from mailmanclient.restobjects.member import Member
from mailmanclient.restobjects.settings import Settings
from mailmanclient.restobjects.held_message import HeldMessage
from mailmanclient.restobjects.templates import TemplateList
from mailmanclient.restbase.base import RESTObject
from mailmanclient.restbase.page import Page

__metaclass__ = type
__all__ = [
    'MailingList'
]


class MailingList(RESTObject):

    _properties = ('display_name', 'fqdn_listname', 'list_id', 'list_name',
                   'mail_host', 'member_count', 'volume', 'self_link',
                   'description')

    def __init__(self, connection, url, data=None):
        super(MailingList, self).__init__(connection, url, data)
        self._settings = None

    def __repr__(self):
        return '<List {0!r}>'.format(self.fqdn_listname)

    @property
    def owners(self):
        url = self._url + '/roster/owner'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        else:
            return [Member(self._connection, entry['self_link'], entry)
                    for entry in sorted(content['entries'],
                                        key=itemgetter('address'))]

    @property
    def moderators(self):
        url = self._url + '/roster/moderator'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        else:
            return [Member(self._connection, entry['self_link'], entry)
                    for entry in sorted(content['entries'],
                                        key=itemgetter('address'))]

    @property
    def members(self):
        url = 'lists/{0}/roster/member'.format(self.fqdn_listname)
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        return [Member(self._connection, entry['self_link'], entry)
                for entry in sorted(content['entries'],
                                    key=itemgetter('address'))]

    @property
    def nonmembers(self):
        url = 'members/find'
        data = {'role': 'nonmember',
                'list_id': self.list_id}
        response, content = self._connection.call(url, data)
        if 'entries' not in content:
            return []
        return [Member(self._connection, entry['self_link'], entry)
                for entry in sorted(content['entries'],
                                    key=itemgetter('address'))]

    def get_member_page(self, count=50, page=1):
        url = 'lists/{0}/roster/member'.format(self.fqdn_listname)
        return Page(self._connection, url, Member, count, page)

    def find_members(self, address=None, role=None, page=None, count=50):
        data = {'list_id': self.list_id}
        if address:
            data['subscriber'] = address
        if role:
            data['role'] = role

        url = 'members/find?{}'.format(urlencode(data, doseq=True))
        if page is None:
            response, content = self._connection.call(url, data)
            if 'entries' not in content:
                return []
            return [Member(self._connection, entry['self_link'], entry)
                    for entry in content['entries']]
        else:
            return Page(self._connection, url, Member, count, page)

    @property
    def settings(self):
        if self._settings is None:
            self._settings = Settings(
                self._connection,
                'lists/{0}/config'.format(self.fqdn_listname))
        return self._settings

    @property
    def held(self):
        """Return a list of dicts with held message information."""
        response, content = self._connection.call(
            'lists/{0}/held'.format(self.fqdn_listname), None, 'GET')
        if 'entries' not in content:
            return []
        return [HeldMessage(self._connection, entry['self_link'], entry)
                for entry in content['entries']]

    def get_held_page(self, count=50, page=1):
        url = 'lists/{0}/held'.format(self.fqdn_listname)
        return Page(self._connection, url, HeldMessage, count, page)

    def get_held_message(self, held_id):
        url = 'lists/{0}/held/{1}'.format(self.fqdn_listname, held_id)
        return HeldMessage(self._connection, url)

    @property
    def requests(self):
        """Return a list of dicts with subscription requests."""
        response, content = self._connection.call(
            'lists/{0}/requests'.format(self.fqdn_listname), None, 'GET')
        if 'entries' not in content:
            return []
        else:
            entries = []
            for entry in content['entries']:
                request = dict(email=entry['email'],
                               token=entry['token'],
                               token_owner=entry['token_owner'],
                               list_id=entry['list_id'],
                               request_date=entry['when'])
                entries.append(request)
        return entries

    @property
    def archivers(self):
        url = 'lists/{0}/archivers'.format(self.list_id)
        return ListArchivers(self._connection, url, self)

    @archivers.setter
    def archivers(self, new_value):
        url = 'lists/{0}/archivers'.format(self.list_id)
        archivers = ListArchivers(self._connection, url, self)
        archivers.update(new_value)
        archivers.save()

    def add_owner(self, address, display_name=None):
        self.add_role('owner', address, display_name)

    def add_moderator(self, address, display_name=None):
        self.add_role('moderator', address, display_name)

    def add_role(self, role, address, display_name=None):
        data = dict(list_id=self.list_id,
                    subscriber=address,
                    display_name=display_name,
                    role=role)
        self._connection.call('members', data)

    def remove_owner(self, address):
        self.remove_role('owner', address)

    def remove_moderator(self, address):
        self.remove_role('moderator', address)

    def remove_role(self, role, address):
        url = 'lists/%s/%s/%s' % (
            self.fqdn_listname, role, quote_plus(address))
        self._connection.call(url, method='DELETE')

    def moderate_message(self, request_id, action):
        """Moderate a held message.

        :param request_id: Id of the held message.
        :type request_id: Int.
        :param action: Action to perform on held message.
        :type action: String.
        """
        path = 'lists/{0}/held/{1}'.format(
            self.fqdn_listname, str(request_id))
        response, content = self._connection.call(
            path, dict(action=action), 'POST')
        return response

    def discard_message(self, request_id):
        """Shortcut for moderate_message."""
        return self.moderate_message(request_id, 'discard')

    def reject_message(self, request_id):
        """Shortcut for moderate_message."""
        return self.moderate_message(request_id, 'reject')

    def defer_message(self, request_id):
        """Shortcut for moderate_message."""
        return self.moderate_message(request_id, 'defer')

    def accept_message(self, request_id):
        """Shortcut for moderate_message."""
        return self.moderate_message(request_id, 'accept')

    def moderate_request(self, request_id, action):
        """
        Moderate a subscription request.

        :param action: accept|reject|discard|defer
        :type action: str.
        """
        path = 'lists/{0}/requests/{1}'.format(self.list_id, request_id)
        response, content = self._connection.call(path, {'action': action})
        return response

    def manage_request(self, token, action):
        """Alias for moderate_request, kept for compatibility"""
        warnings.warn(
            'The `manage_request()` method has been replaced by '
            '`moderate_request()` and will be removed in the future.',
            DeprecationWarning, stacklevel=2)
        return self.moderate_request(token, action)

    def accept_request(self, request_id):
        """Shortcut to accept a subscription request."""
        return self.moderate_request(request_id, 'accept')

    def reject_request(self, request_id):
        """Shortcut to reject a subscription request."""
        return self.moderate_request(request_id, 'reject')

    def discard_request(self, request_id):
        """Shortcut to discard a subscription request."""
        return self.moderate_request(request_id, 'discard')

    def defer_request(self, request_id):
        """Shortcut to defer a subscription request."""
        return self.moderate_request(request_id, 'defer')

    def get_member(self, email):
        """Get a membership.

        :param address: The email address of the member for this list.
        :return: A member proxy object.
        """
        # In order to get the member object we query the REST API for
        # the member. Incase there is no matching subscription, an
        # HTTPError is returned instead.
        try:
            path = 'lists/{0}/member/{1}'.format(
                self.list_id, quote_plus(email))
            response, content = self._connection.call(path)
            return Member(self._connection, content['self_link'], content)
        except HTTPError:
            raise ValueError('%s is not a member address of %s' %
                             (email, self.fqdn_listname))

    def subscribe(self, address, display_name=None, pre_verified=False,
                  pre_confirmed=False, pre_approved=False):
        """Subscribe an email address to a mailing list.

        :param address: Email address to subscribe to the list.
        :type address: str
        :param display_name: The real name of the new member.
        :param pre_verified: True if the address has been verified.
        :type pre_verified: bool
        :param pre_confirmed: True if membership has been approved by the user.
        :type pre_confirmed: bool
        :param pre_approved: True if membership is moderator-approved.
        :type pre_approved: bool
        :type display_name: str
        :return: A member proxy object.
        """
        data = dict(
            list_id=self.list_id,
            subscriber=address,
            display_name=display_name,
        )
        if pre_verified:
            data['pre_verified'] = True
        if pre_confirmed:
            data['pre_confirmed'] = True
        if pre_approved:
            data['pre_approved'] = True
        response, content = self._connection.call('members', data)
        # If a member is not immediately subscribed (i.e. verificatoin,
        # confirmation or approval need), the response content is returned.
        if response.status_code == 202:
            return content
        # I the subscription is executed immediately, a member object
        # is returned.
        return Member(self._connection, response.headers.get('location'))

    def unsubscribe(self, email):
        """Unsubscribe an email address from a mailing list.

        :param address: The address to unsubscribe.
        """
        try:
            path = 'lists/{0}/member/{1}'.format(self.list_id, email)
            self._connection.call(path, method='DELETE')
        except HTTPError:
            # The member link does not exist, i.e. he is not a member
            raise ValueError('%s is not a member address of %s' %
                             (email, self.fqdn_listname))

    def mass_unsubscribe(self, email_list):
        """Unsubscribe a list of emails from a mailing list.

        This function return a json of emails mapped to booleans based
        on whether they were unsubscribed or not, for whatever reasons

        :param email_list: list of emails to unsubscribe
        """
        try:
            path = 'lists/{}/roster/member'.format(self.list_id)
            response, content = self._connection.call(
                path, {'emails': email_list}, 'DELETE')
            return content
        except HTTPError as e:
            raise ValueError(str(e))

    @property
    def bans(self):
        from mailmanclient.restobjects.ban import Bans
        url = 'lists/{0}/bans'.format(self.list_id)
        return Bans(self._connection, url, mlist=self)

    def get_bans_page(self, count=50, page=1):
        from mailmanclient.restobjects.ban import BannedAddress
        url = 'lists/{0}/bans'.format(self.list_id)
        return Page(self._connection, url, BannedAddress, count, page)

    @property
    def header_matches(self):
        url = 'lists/{0}/header-matches'.format(self.list_id)
        return HeaderMatches(self._connection, url, self)

    @property
    def templates(self):
        url = self._url + '/uris'
        return TemplateList(self._connection, url)

    def set_template(self, template_name, uri, username=None, password=None):
        url = self._url + '/uris'
        data = {template_name: uri}
        if username is not None and password is not None:
            data['username'] = username
            data['password'] = password
        return self._connection.call(url, data, 'PATCH')[1]

    def _check_membership(self, address, allowed_roles):
        """
        Given an address and role, check if there is a membership record that
        matches the given address with a given role for this Mailing List.
        """
        url = 'members/find'
        data = {'subscriber': address,
                'list_id': self.list_id}
        response, content = self._connection.call(url, data=data)
        if 'entries' not in content:
            return False
        for membership in content['entries']:
            # We check for all the returned roles for this User and MailingList
            if membership['role'] in allowed_roles:
                return True
        return False

    def is_owner(self, address):
        """
        Given an address, checks if the given address is an owner of this
        mailing list.
        """
        return self._check_membership(address=address,
                                      allowed_roles=('owner',))

    def is_moderator(self, address):
        """
        Given an address, checks if the given address is a moderator of this
        mailing list.
        """
        return self._check_membership(address=address,
                                      allowed_roles=('moderator',))

    def is_member(self, address):
        """
        Given an address, checks if the given address is subscribed to this
        mailing list.
        """
        return self._check_membership(address=address,
                                      allowed_roles=('member',))

    def is_owner_or_mod(self, address):
        """
        Given an address, checks if the given address is either a owner or
        a moderator of this list.

        It is possible for them to be both owner and moderator.
        """
        return self._check_membership(address=address,
                                      allowed_roles=('owner', 'moderator'))
