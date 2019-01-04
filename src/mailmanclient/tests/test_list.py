# Copyright (C) 2017-2019 by the Free Software Foundation, Inc.
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

"""Tests for Mailing List."""

from __future__ import absolute_import, print_function, unicode_literals

from urllib.error import HTTPError
from unittest import TestCase
from mailmanclient import Client


class TestMailingListMembershipTests(TestCase):

    def setUp(self):
        self._client = Client(
            'http://localhost:9001/3.1', 'restadmin', 'restpass')
        try:
            self.domain = self._client.create_domain('example.com')
        except HTTPError:
            self.domain = self._client.get_domain('example.com')
        self.mlist = self.domain.create_list('foo')

    def tearDown(self):
        self.domain.delete()

    def test_list_is_owner(self):
        # Tests MailingList.is_owner
        # First, we add an owner to the mailing list and then make sure that
        # we see it in the owners roster.
        anne_addr = 'ann@example.com'
        self.mlist.add_owner(anne_addr)
        # Check that the address
        owners_list = [owner.email for owner in self.mlist.owners]
        self.assertIn(anne_addr, owners_list)
        # Now, we make sure that we get the same result in our API.
        self.assertTrue(self.mlist.is_owner(anne_addr))
        # Make sure we get False for someone who is not a list owner.
        self.assertFalse(self.mlist.is_owner('random@example.com'))
        # Make sure that a subscriber doesn't return True for is_owner check.
        # We are doing this test because of the way is_owner test works. A
        # wrong value for `role` could result in a list member being tested
        # as owner.
        self.mlist.subscribe('bart@example.com')
        self.assertFalse(self.mlist.is_owner('bart@example.com'))
        # Now, try the same thing for Moderators.
        self.mlist.add_moderator('mod@example.com')
        self.assertFalse(self.mlist.is_owner('mod@example.com'))

    def test_list_is_moderator(self):
        # Tests MailingList.is_moderator
        # First, we add a moderator to the list.
        mod_addr = 'mod@example.com'
        self.mlist.add_moderator(mod_addr)
        mods_emails = [mod.email for mod in self.mlist.moderators]
        self.assertIn(mod_addr, mods_emails)
        self.assertFalse(self.mlist.is_owner(mod_addr))
        # Owners shouldn't return true for this API.
        owner_addr = 'owner@example.com'
        self.mlist.add_owner(owner_addr)
        self.assertFalse(self.mlist.is_moderator(owner_addr))
        # Subscribers shouldn't return true for this API.
        subscriber_addr = 'subscriber@example.com'
        self.mlist.subscribe(subscriber_addr)
        self.assertFalse(self.mlist.is_moderator(subscriber_addr))

    def test_list_is_member(self):
        # Tests MailingList.is_member
        subscriber_addr = 'subscriber@example.com'
        self.mlist.subscribe(subscriber_addr, pre_verified=True,
                             pre_confirmed=True, pre_approved=True)
        all_subscribers = [member.email for member in self.mlist.members]
        self.assertIn(subscriber_addr, all_subscribers)
        # Now make sure we get the same result through this API.
        self.assertTrue(self.mlist.is_member(subscriber_addr))
        # Make sure owners don't pass this check.
        owner_addr = 'owner@example.com'
        self.mlist.add_owner(owner_addr)
        self.assertFalse(self.mlist.is_member(owner_addr))
        # Make sure moderators don't pass this check.
        mod_addr = 'mod@example.com'
        self.mlist.add_moderator(mod_addr)
        self.assertFalse(self.mlist.is_member(mod_addr))

    def test_list_is_owner_or_mod(self):
        # Tests MailingList.is_owner_or_mod
        # Tests MailingList.is_moderator
        # First, we add a moderator to the list.
        mod_addr = 'mod@example.com'
        self.mlist.add_moderator(mod_addr)
        mods_emails = [mod.email for mod in self.mlist.moderators]
        self.assertIn(mod_addr, mods_emails)
        self.assertTrue(self.mlist.is_owner_or_mod(mod_addr))
        # Owners shouldn't return true for this API.
        owner_addr = 'owner@example.com'
        self.mlist.add_owner(owner_addr)
        owners_list = [owner.email for owner in self.mlist.owners]
        self.assertIn(owner_addr, owners_list)
        self.assertTrue(self.mlist.is_owner_or_mod(owner_addr))
        # Subscribers shouldn't return true for this API.
        subscriber_addr = 'subscriber@example.com'
        self.mlist.subscribe(subscriber_addr)
        self.assertFalse(self.mlist.is_owner_or_mod(subscriber_addr))
