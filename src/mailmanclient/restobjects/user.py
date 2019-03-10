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


from mailmanclient.restobjects.preferences import PreferencesMixin
from mailmanclient.restobjects.address import Addresses, Address
from mailmanclient.restbase.base import RESTObject

__metaclass__ = type
__all__ = [
    'User'
]


class User(RESTObject, PreferencesMixin):

    _properties = ('created_on', 'display_name', 'is_server_owner',
                   'password', 'self_link', 'user_id')
    _writable_properties = ('cleartext_password', 'display_name',
                            'is_server_owner')

    def __init__(self, connection, url, data=None):
        super(User, self).__init__(connection, url, data)
        self._subscriptions = None
        self._subscription_list_ids = None

    def __repr__(self):
        return '<User {0!r} ({1})>'.format(self.display_name, self.user_id)

    @property
    def addresses(self):
        return Addresses(
            self._connection, 'users/{0}/addresses'.format(self.user_id))

    def __setattr__(self, name, value):
        """Special case for the password"""
        if name == 'password':
            self._changed_rest_data['cleartext_password'] = value
            if self._autosave:
                self.save()
        else:
            super(User, self).__setattr__(name, value)

    @property
    def subscriptions(self):
        from mailmanclient.restobjects.member import Member
        if self._subscriptions is None:
            subscriptions = []
            for address in self.addresses:
                response, content = self._connection.call(
                    'members/find', data={'subscriber': address})
                try:
                    for entry in content['entries']:
                        subscriptions.append(Member(
                            self._connection, entry['self_link'], entry))
                except KeyError:
                    pass
            self._subscriptions = subscriptions
        return self._subscriptions

    @property
    def subscription_list_ids(self):
        if self._subscription_list_ids is None:
            list_ids = []
            for sub in self.subscriptions:
                list_ids.append(sub.list_id)
            self._subscription_list_ids = list_ids
        return self._subscription_list_ids

    def add_address(self, email, absorb_existing=False):
        """
        Adds another email adress to the user record and returns an
        _Address object.

        :param email: The address to add
        :type  email: str.
        :param absorb_existing: set this to True if you want to add the address
            even if it already exists. It will import the existing user into
            the current one, not overwriting any previously set value.
        :type  absorb_existing: bool.
        """
        url = '{0}/addresses'.format(self._url)
        data = {'email': email}
        if absorb_existing:
            data['absorb_existing'] = 1
        response, content = self._connection.call(url, data)
        address = {
            'email': email,
            'self_link': response.headers.get('location'),
        }
        return Address(self._connection, address['self_link'], address)
