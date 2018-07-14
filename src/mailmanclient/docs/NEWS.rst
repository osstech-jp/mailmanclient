=======================
NEWS for mailmanclient
=======================

3.2.1 (201X-XX-XX)
==================

* Add support for Python 3.7



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



Backwards Incompatible Changes
-------------------------------

* `Domain.owners` now returns a list of `User` objects instead of just a dictionary of
  JSON response. (!63)

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
