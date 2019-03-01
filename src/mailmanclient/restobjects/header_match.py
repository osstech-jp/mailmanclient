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
from mailmanclient.restbase.base import RESTList, RESTObject

__metaclass__ = type
__all__ = [
    'HeaderMatch',
    'HeaderMatches'
]


class HeaderMatches(RESTList):
    """
    The list of header matches for a mailing-list.
    """

    def __init__(self, connection, url, mlist):
        """
        :param mlist: The corresponding list object.
        :type mlist: MailingList.
        """
        super(HeaderMatches, self).__init__(connection, url)
        self._mlist = mlist
        self._factory = lambda data: HeaderMatch(
            self._connection, data['self_link'], data)

    def __repr__(self):
        return '<HeaderMatches for {0!r}>'.format(self._mlist.list_id)

    def __str__(self):
        return 'Header matches for "{}"'.format(self._mlist.list_id)

    def add(self, header, pattern, action=None):
        """
        :param header: The header to consider.
        :type  header: str
        :param pattern: The regular expression to use for filtering.
        :type  pattern: str
        :param action: The action to take when the header matches the pattern.
            This can be 'accept', 'discard', 'reject', or 'hold'.
        :type  action: str
        """
        data = dict(header=header, pattern=pattern)
        if action is not None:
            data['action'] = action
        response, content = self._connection.call(self._url, data)
        self._reset_cache()
        return HeaderMatch(self._connection, response.headers.get('location'))


class HeaderMatch(RESTObject):

    _properties = ('header', 'pattern', 'position', 'action', 'self_link')
    _writable_properties = ('header', 'pattern', 'position', 'action')

    def __repr__(self):
        return '<HeaderMatch on {0!r}>'.format(self.header)

    def __str__(self):
        return 'Header match on "{}"'.format(self.header)
