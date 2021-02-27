=======================
NEWS for mailmanclient
=======================


.. _news-3.3.3:

3.3.3 (2021-XX-XX)
==================
- Add ``pre_confirmed`` and ``pre_approved`` parameters to
  ``MailingList.unsubscribe``. (Fixes :issue:`62`)
- Add support to fetch pending unsubscription requests. (Closes :issue:`63`)
- Add ``member_id`` as a property of ``Member`` object. (Closes :issue:`64`)
- Return pending token when a Member is unsubscribed. (Closes :issue:`65`)
- Allow specifying a reason when handling subscription requests (Closes :issue:`66`)
- Add support to specify fields when fetching a roster. (Closes :issue:`67`)
- Add a mechanism to hook into the request parameters. (Closes :issue:`68`)


.. _news-3.3.2:

3.3.2 (2021-01-10)
==================

- Add two new ``get_requests()`` and ``get_requests_count()`` to get pending
  subscription requests``MailingList.get_requests`` is the new API to fetch
  pending requests and supersedes the previous ``requests`` property. (See
  :pr:`121`)
- Add ``Member.subscription_mode`` to determine if a User is subscribed or an
  Address. (See :pr:`121`)
- Add a new ``get_held_count()`` API to get a count of held messages for a
  ``MailingList``. (See :pr:`122`)
- Add ``display_name`` to the pending subscription requests. (Fixes :issue:`55`)
- Allow setting a ``Member``'s ``address`` attribute. (See :pr:`128`)
- Add support for inviting an email address to join a list.
- Rewrite urls according to the ``baseurl`` used to instantiate ``Client``
  instead of relying on ``self_link``. (Fixes :issue:`22`)
- Add ``get_request`` API to MailingList to get individual request objects.
- Add ``send_welcome_message`` parameter to MailingList.subscribe() to suppress
  welcome message. (Closes :issue:`61`)

3.3.1 (2020-06-01)
==================

- Held message moderation now supports an optional keyword, ``reason`` to
  specify the reason to reject the message. (Closes :issue:`49`)
- Fix a bug where missing ``display_name`` attribute with
  ``MalingList.subscribe`` would subscribe the user with a display name of
  "None". (Fixes :issue:`52`)
- Add ``advertised`` flag to ``MailingList`` object. (See :pr:`115`)
- ``MailingList.nonmembers`` now uses ``roster/nonmembers`` resource instead of
  the ``find/`` API for consistency.
- Add ``Client.get_nonmember`` and ``MailingList.get_nonmember`` to get a
  non-member by address. (Fixes :issue:`47`)

3.3.0 (2019-09-03)
==================

* Add a ``mail_host`` parameter to ``get_list_page`` and ``find_lists`` to
  support filtering the response by a list domain.
* URL encode values in URL which are url unsafe. (Closes :issue:`44`)
* Add support to mass unsubscribe memebrs from a Mailing List. (Closes :issue:`43`)
* Add support to set a user's preferred address. (See :pr:`99`)
* Add a new ``tag`` attribute to HeaderMatches and support to find a set
	of matches based on tag.

3.2.2 (2019-02-09)
==================


3.2.1 (2019-01-04)
==================

* Add support for Python 3.7
* Add ``description`` as a property of ``MailingList``. Initially, this was a
  part of ``Preferences`` object, which would mean an additional API call to get
  the description of a Mailing List. (Closes :issue:`35`)
* ``MailingList.get_members`` no longer requires ``address`` as a mandatory
  argument which allows searching for all memberships of of a particular role. 
  Also, ``role`` no longer has a default argument, so that we can search for
  all memberships of an address.


3.2.0 (2018-07-10)
==================

Changes
-------

* Add '.pc' (patch directory) to list of ignored patterns when building the
  documentation with Sphinx.
* `Mailinglist.add_owner` and `Mailinglist.add_moderator` now accept an
  additional `display_name` argument that allows associating display names with
  these memberships.
* Add a new API ``Client.find_lists`` which allows filtering mailing lists
  related to a subscriber. It optionally allows a role, which filters the lists
  that the address is subscribed to with that role.

Backwards Incompatible Changes
-------------------------------

* `MailingList.owners` and `MailingList.moderators` now returns a list of
  `Member` objects instead of a list of emails.
* `Domain.owners` now returns a list of `User` objects instead of just a dictionary of
  JSON response. (:pr:`63`)
* Python 2.7 is no longer supported.

3.1.1 (2017-10-07)
==================

 * Python3 compatibility is fixed, mailmanclient is now compatible through Python2.7 - Python3.6
 * Internal source code is now split into several class-specific modules as
   compared to previously a single giant _client module.
 * All the RestObjects, like MailingList, are now exposed from the top level import.
 * Old `mailmanclient._client` module is added back for compatibility with
   versions of Postorius that use some internal APIs.


3.1 (2017-05-25)
================

 * Bug fixes.
 * Align with Mailman 3.1 Core REST API.
 * Python3 compatibility is broken because of a urllib bug.


1.0.1 (2015-11-14)
==================

 * Bugfix release.


1.0.0 (2015-04-17)
==================

 * Port to Python 3.4.
 * Run test suite with `tox`.
 * Use vcrpy for HTTP testing.
 * Add list archiver access.
 * Add subscription moderation


1.0.0a1 (2014-03-15)
====================

 * Initial release.
