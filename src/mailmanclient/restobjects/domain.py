# Copyright (C) 2010-2017 The Free Software Foundation, Inc.
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

from mailmanclient.restobjects.mailinglist import MailingList
from mailmanclient.restbase.base import RESTObject
from mailmanclient.restbase.page import Page

__metaclass__ = type
__all__ = [
    'Domain'
]


class Domain(RESTObject):

    _properties = ('alias_domain', 'description', 'mail_host', 'self_link')

    def __repr__(self):
        return '<Domain "{0}">'.format(self.mail_host)

    @property
    def web_host(self):
        warnings.warn(
            'The `Domain.web_host` attribute is deprecated. It is not used '
            'any more and will be removed in the future.',
            DeprecationWarning, stacklevel=2)
        return 'http://{}'.format(self.mail_host)

    @property
    def base_url(self):
        warnings.warn(
            'The `Domain.base_url` attribute is deprecated. It is not used '
            'any more and will be removed in the future.',
            DeprecationWarning, stacklevel=2)
        return 'http://{}'.format(self.mail_host)

    @property
    def owners(self):
        url = self._url + '/owners'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        else:
            return [item for item in content['entries']]

    @property
    def lists(self):
        return self.get_lists()

    def get_lists(self, advertised=None):
        url = 'domains/{0}/lists'.format(self.mail_host)
        if advertised:
            url += '?advertised=true'
        response, content = self._connection.call(url)
        if 'entries' not in content:
            return []
        return [MailingList(self._connection, entry['self_link'], entry)
                for entry in content['entries']]

    def get_list_page(self, count=50, page=1, advertised=None):
        url = 'domains/{0}/lists'.format(self.mail_host)
        if advertised:
            url += '?advertised=true'
        return Page(self._connection, url, MailingList, count, page)

    def create_list(self, list_name):
        fqdn_listname = '{0}@{1}'.format(list_name, self.mail_host)
        response, content = self._connection.call(
            'lists', dict(fqdn_listname=fqdn_listname))
        return MailingList(self._connection, response['location'])

    # def remove_owner(self, owner):
    #     TODO: add this when API supports it.
    #     pass

    def remove_all_owners(self):
        url = self._url + '/owners'
        response, content = self._connection.call(
            url, method='DELETE')
        return response

    def add_owner(self, owner):
        url = self._url + '/owners'
        response, content = self._connection.call(
            url, {'owner': owner})
