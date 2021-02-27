=============
Example Usage
=============

This is the official Python bindings for the GNU Mailman REST API.  In order
to talk to Mailman, the engine's REST server must be running.  You begin by
instantiating a client object to access the root of the REST hierarchy,
providing it the base URL, user name and password (for Basic Auth).

    >>> from mailmanclient import Client
    >>> client = Client('http://localhost:9001/3.1', 'restadmin', 'restpass')

.. note::
    Please note that port '9001' is used above, since mailman's test server
    runs on port *9001*. In production Mailman's REST API usually listens on
    port *8001*.

We can retrieve basic information about the server.

    >>> dump(client.system)
    api_version: 3.1
    http_etag: "..."
    mailman_version: GNU Mailman ... (...)
    python_version: ...
    self_link: http://localhost:9001/3.1/system/versions

.. note::
    The content accessible via mailmanclient depends heavily on the version
    of the mailman core REST API it's connecting to. See `Core REST API
    docs`_ for more details.

To start with, there are no known mailing lists.

    >>> client.lists
    []


Domains
=======

Before new mailing lists can be added, the domain that the list will live in
must be added.  By default, there are no known domains.

    >>> client.domains
    []

It's easy to create a new domain; when you do, a proxy object for that domain
is returned.

    >>> example_dot_com = client.create_domain('example.com')
    >>> print(example_dot_com.description)
    None
    >>> print(example_dot_com.mail_host)
    example.com
    >>> print(example_dot_com.alias_domain)
    None

A domain can have an alias_domain attribute to help with some unusual Postfix
configurations.

    >>> example_dot_edu = client.create_domain('example.edu',
    ...                                        alias_domain='x.example.edu')
    >>> print(example_dot_edu.mail_host)
    example.edu
    >>> print(example_dot_edu.alias_domain)
    x.example.edu

You can also get an existing domain independently using its mail host.

    >>> example = client.get_domain('example.com')
    >>> print(example.mail_host)
    example.com

After creating a few more domains, we can print the list of all domains.

    >>> example_net = client.create_domain('example.net')
    >>> example_org = client.create_domain('example.org')
    >>> print(example_org.mail_host)
    example.org
    >>> for domain in client.domains:
    ...     print(domain.mail_host)
    example.com
    example.edu
    example.net
    example.org

Also, domain can be deleted.

    >>> example_org.delete()
    >>> for domain in client.domains:
    ...     print(domain.mail_host)
    example.com
    example.edu
    example.net


Mailing lists
=============

Once you have a domain, you can create mailing lists in that domain.

    >>> test_one = example.create_list('test-1')
    >>> print(test_one.fqdn_listname)
    test-1@example.com
    >>> print(test_one.mail_host)
    example.com
    >>> print(test_one.list_name)
    test-1
    >>> print(test_one.display_name)
    Test-1

You can create a mailing list with a specific list style.

    >>> test_two = example.create_list('test-announce', style_name='legacy-announce')
    >>> print(test_two.fqdn_listname)
    test-announce@example.com

You can retrieve a list of known mailing list styles along with the default
one.

    >>> styles = client.styles
    >>> from operator import itemgetter
    >>> for style in sorted(styles['styles'], key=itemgetter('name')):
    ...     print('{0}: {1}'.format(style['name'], style['description']))
    legacy-announce: Announce only mailing list style.
    legacy-default: Ordinary discussion mailing list style.
    private-default: Discussion mailing list style with private archives.
    >>> print(styles['default'])
    legacy-default

You can also retrieve the mailing list after the fact.

    >>> my_list = client.get_list('test-1@example.com')
    >>> print(my_list.fqdn_listname)
    test-1@example.com

And you can print all the known mailing lists.
::

    >>> print(example.create_list('test-2').fqdn_listname)
    test-2@example.com
    >>> domain = client.get_domain('example.net')
    >>> print(domain.create_list('test-3').fqdn_listname)
    test-3@example.net
    >>> print(example.create_list('test-3').fqdn_listname)
    test-3@example.com

    >>> for mlist in client.lists:
    ...     print(mlist.fqdn_listname)
    test-1@example.com
    test-2@example.com
    test-3@example.com
    test-3@example.net
    test-announce@example.com

You can also select advertised lists only.
::

    >>> my_list.settings['advertised'] = False
    >>> my_list.settings.save()
    >>> for mlist in client.get_lists(advertised=True):
    ...     print(mlist.fqdn_listname)
    test-2@example.com
    test-3@example.com
    test-3@example.net
    test-announce@example.com

List results can be retrieved as pages:

    >>> page = client.get_list_page(count=2, page=1)
    >>> page.nr
    1
    >>> len(page)
    2
    >>> page.total_size
    5
    >>> for m_list in page:
    ...     print(m_list.fqdn_listname)
    test-1@example.com
    test-2@example.com
    >>> page = page.next
    >>> page.nr
    2
    >>> for m_list in page:
    ...     print(m_list.fqdn_listname)
    test-3@example.com
    test-3@example.net

Pages can also use the advertised filter:

    >>> page = client.get_list_page(count=2, page=1, advertised=True)
    >>> for m_list in page:
    ...     print(m_list.fqdn_listname)
    test-2@example.com
    test-3@example.com

Pages can also limit the results by domain:

    >>> page = client.get_list_page(mail_host='example.net')
    >>> for m_list in page:
    ...     print(m_list.fqdn_listname)
    test-3@example.net

You can also use the domain object if you only want to know all lists for a
specific domain without pagination.

    >>> for mlist in example.lists:
    ...     print(mlist.fqdn_listname)
    test-1@example.com
    test-2@example.com
    test-3@example.com
    test-announce@example.com

It is also possible to display only advertised lists when using the domain.

    >>> for mlist in example.get_lists(advertised=True):
    ...     print(mlist.fqdn_listname)
    test-2@example.com
    test-3@example.com
    test-announce@example.com
    >>> for mlist in example.get_list_page(count=2, page=1, advertised=True):
    ...     print(mlist.fqdn_listname)
    test-2@example.com
    test-3@example.com

You can use a list instance to delete the list.

    >>> test_three = client.get_list('test-3@example.net')
    >>> test_three.delete()

You can also delete a list using the client instance's delete_list method.

    >>> client.delete_list('test-3@example.com')

    >>> for mlist in client.lists:
    ...     print(mlist.fqdn_listname)
    test-1@example.com
    test-2@example.com
    test-announce@example.com

Membership
==========

Email addresses can subscribe to existing mailing lists, becoming members of
that list.  The address is a unique id for a specific user in the system, and
a member is a user that is subscribed to a mailing list.  Email addresses need
not be pre-registered, though the auto-registered user will be unique for each
email address.

The system starts out with no members.

    >>> client.members
    []

New members can be easily added; users are automatically registered.
::

    >>> test_two = client.get_list('test-2@example.com')
    >>> print(test_two.settings['subscription_policy'])
    confirm

Email addresses need to be verified first, so if we try to subscribe a
user, we get a response with a token:

    >>> data = test_one.subscribe('unverified@example.com', 'Unverified')
    >>> data['token'] is not None
    True
    >>> print(data['token_owner'])
    subscriber

We can also invite an email address to join the list.  This will send an
invitation email to the address for the user to accept.  Here again we get a
response with a token:

    >>> data = test_one.subscribe('invitee@example.com',
    ...                           'Invitee',
    ...                           invitation=True)
    >>> data['token'] is not None
    True
    >>> print(data['token_owner'])
    subscriber

If we know the email address to be valid, we can set the
``pre_verified`` flag. However, the list's subscription policy is
"confirm", so if we try to subscribe a user, we will also get a token
back:

    >>> data = test_one.subscribe('unconfirmed@example.com',
    ...                           'Unconfirmed',
    ...                            pre_verified=True)
    >>> data['token'] is not None
    True
    >>> print(data['token_owner'])
    subscriber

If we know the user originated the subscription (for example if she or
he has been authenticated elsewhere), we can set the ``pre_confirmed``
flag.

The ``pre_approved`` flag is used for lists that require moderator
approval and should only be used if the subscription is initiated by a
moderator or admin.

    >>> print(test_one.subscribe('anna@example.com', 'Anna',
    ...                          pre_verified=True,
    ...                          pre_confirmed=True))
    Member "anna@example.com" on "test-1.example.com"

    >>> print(test_one.subscribe('bill@example.com', 'Bill',
    ...                          pre_verified=True,
    ...                          pre_confirmed=True))
    Member "bill@example.com" on "test-1.example.com"

    >>> print(test_two.subscribe('anna@example.com',
    ...                          pre_verified=True,
    ...                          pre_confirmed=True))
    Member "anna@example.com" on "test-2.example.com"

    >>> print(test_two.subscribe('cris@example.com', 'Cris',
    ...                          pre_verified=True,
    ...                          pre_confirmed=True))
    Member "cris@example.com" on "test-2.example.com"

We can retrieve all known memberships.  These are sorted first by mailing list
name, then by email address.

    >>> for member in client.members:
    ...     print(member)
    Member "anna@example.com" on "test-1.example.com"
    Member "bill@example.com" on "test-1.example.com"
    Member "anna@example.com" on "test-2.example.com"
    Member "cris@example.com" on "test-2.example.com"

We can also view the memberships for a single mailing list.

    >>> for member in test_one.members:
    ...     print(member)
    Member "anna@example.com" on "test-1.example.com"
    Member "bill@example.com" on "test-1.example.com"

Membership may have a name associated, this depends on whether the member ``Address``
or ``User`` has a ``display_name`` attribute.

    >>> for member in test_one.members:
    ...     print(member.display_name)
    Anna
    Bill

Membership lists can be paginated, to recieve only a part of the result.

    >>> page = client.get_member_page(count=2, page=1)
    >>> page.nr
    1
    >>> page.total_size
    4
    >>> for member in page:
    ...     print(member)
    Member "anna@example.com" on "test-1.example.com"
    Member "bill@example.com" on "test-1.example.com"

    >>> page = page.next
    >>> page.nr
    2
    >>> for member in page:
    ...     print(member)
    Member "anna@example.com" on "test-2.example.com"
    Member "cris@example.com" on "test-2.example.com"

    >>> page = test_one.get_member_page(count=1, page=1)
    >>> page.nr
    1
    >>> page.total_size
    2
    >>> for member in page:
    ...     print(member)
    Member "anna@example.com" on "test-1.example.com"
    >>> page = page.next
    >>> page.nr
    2
    >>> page.total_size
    2
    >>> for member in page:
    ...     print(member)
    Member "bill@example.com" on "test-1.example.com"

We can get a single membership too.

    >>> cris_test_two = test_two.get_member('cris@example.com')
    >>> print(cris_test_two)
    Member "cris@example.com" on "test-2.example.com"
    >>> print(cris_test_two.role)
    member
    >>> print(cris_test_two.display_name)
    Cris

A membership can also be retrieved without instantiating the list object first:

    >>> print(client.get_member('test-2@example.com', 'cris@example.com'))
    Member "cris@example.com" on "test-2.example.com"

A membership has preferences.

    >>> prefs = cris_test_two.preferences
    >>> print(prefs['delivery_mode'])
    None
    >>> print(prefs['acknowledge_posts'])
    None
    >>> print(prefs['delivery_status'])
    None
    >>> print(prefs['hide_address'])
    None
    >>> print(prefs['preferred_language'])
    None
    >>> print(prefs['receive_list_copy'])
    None
    >>> print(prefs['receive_own_postings'])
    None

The membership object's ``user`` attribute will return a User object:

    >>> cris_u = cris_test_two.user
    >>> print(cris_u.display_name, cris_u.user_id)
    Cris ...

If you use an address which is not a member of test_two `ValueError` is raised:

    >>> test_two.unsubscribe('nomember@example.com')
    Traceback (most recent call last):
    ...
    ValueError: nomember@example.com is not a member address of test-2@example.com

After a while, Anna decides to unsubscribe from the Test One mailing list,
though she keeps her Test Two membership active.

    >>> import time
    >>> time.sleep(2)
    >>> test_one.unsubscribe('anna@example.com')
    >>> for member in client.members:
    ...     print(member)
    Member "bill@example.com" on "test-1.example.com"
    Member "anna@example.com" on "test-2.example.com"
    Member "cris@example.com" on "test-2.example.com"

A little later, Cris decides to unsubscribe from the Test Two mailing list.

    >>> cris_test_two.unsubscribe()
    >>> for member in client.members:
    ...     print(member)
    Member "bill@example.com" on "test-1.example.com"
    Member "anna@example.com" on "test-2.example.com"

If you try to unsubscribe an address which is not a member address
`ValueError` is raised:

    >>> test_one.unsubscribe('nomember@example.com')
    Traceback (most recent call last):
    ...
    ValueError: nomember@example.com is not a member address of test-1@example.com

If we want to mass unsubscribe users.

    >>> print(test_one.subscribe('jack@example.com', 'Jack',
    ...                          pre_verified=True,
    ...                          pre_confirmed=True))
    Member "jack@example.com" on "test-1.example.com"

    >>> print(test_one.subscribe('jill@example.com', 'Jill',
    ...                          pre_verified=True,
    ...                          pre_confirmed=True))
    Member "jill@example.com" on "test-1.example.com"

    >>> print(test_one.subscribe('hans@example.com', 'Hans',
    ...                          pre_verified=True,
    ...                          pre_confirmed=True))
    Member "hans@example.com" on "test-1.example.com"

    >>> email_list = ['jack@example.com','hans@example.com','jill@example.com','bully@example.com']
    >>> ();test_one.mass_unsubscribe(email_list);() # doctest: +ELLIPSIS
    (...)
    >>> for member in test_one.members:
    ...     print(member)
    Member "bill@example.com" on "test-1.example.com"


Non-Members
===========

When someone attempts to post to a list but is not a member, then they are
listed as a "non-member" of that list so that a moderator can choose how to
handle their messages going forward.  In some cases, one might wish to
accept or reject their future messages automatically.  Just like with regular
members, they are given a unique id.

The list starts out with no nonmembers.

    >>> test_one.nonmembers
    []

When someone tries to send a message to the list and they are not a
subscriber, they get added to the nonmember list.


Users
=====

Users are people with one or more list memberships. To get a list of all users,
access the clients user property.

    >>> for user in client.users:
    ...     print(user.display_name)
    Unverified
    Invitee
    Unconfirmed
    Anna
    Bill
    Cris
    Jack
    Jill
    Hans

The list of users can also be paginated:

    >>> page = client.get_user_page(count=4, page=1)
    >>> page.nr
    1
    >>> page.total_size
    9
    >>> for user in page:
    ...     print(user.display_name)
    Unverified
    Invitee
    Unconfirmed
    Anna

You can get the next or previous pages without calling ``get_userpage`` again.

    >>> page = page.next
    >>> page.nr
    2

    >>> for user in page:
    ...     print(user.display_name)
    Bill
    Cris
    Jack
    Jill

    >>> page = page.previous
    >>> page.nr
    1

    >>> for user in page:
    ...     print(user.display_name)
    Unverified
    Invitee
    Unconfirmed
    Anna

A single user can be retrieved using their email address.

    >>> cris = client.get_user('cris@example.com')
    >>> print(cris.display_name)
    Cris

Every user has a list of one or more addresses.

    >>> for address in cris.addresses:
    ...     print(address)
    ...     print(address.display_name)
    ...     print(address.registered_on)
    cris@example.com
    Cris
    ...

Multiple addresses can be assigned to a user record:

    >>> print(cris.add_address('cris.person@example.org'))
    cris.person@example.org
    >>> print(client.get_address('cris.person@example.org'))
    cris.person@example.org

    >>> for address in cris.addresses:
    ...     print(address)
    cris.person@example.org
    cris@example.com

Trying to add an existing address will raise an error:

    >>> dana = client.create_user(email='dana@example.org',
    ...                           password='somepass',
    ...                           display_name='Dana')
    >>> print(dana.display_name)
    Dana
    >>> cris.add_address('dana@example.org')  # doctest: +IGNORE_EXCEPTION_DETAIL
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 400: Address already exists

This can be overridden by using the ``absorb_existing`` flag:

    >>> print(cris.add_address('dana@example.org', absorb_existing=True))
    dana@example.org

The user Chris will then be merged with Dana, acquiring all its subscriptions
and preferences. In case of conflict, Chris' original preferences will prevail.

    >>> for address in cris.addresses:
    ...     print(address)
    cris.person@example.org
    cris@example.com
    dana@example.org

Users can have one preferred address, which they can use for subscriptions. By
default, a User has no preferred address.

    >>> print(cris.preferred_address)
    None

A User can have a preferred address, but before that, the address needs to be
verified::

    >>> address = client.get_address('cris.person@example.org')
    >>> address.verify()
    >>> print(address.verified)
    True
    >>> cris.preferred_address = 'cris.person@example.org'
    >>> print(cris.preferred_address)
    cris.person@example.org

A User can change their preferred address.

    >>> cris.preferred_address = 'cris@example.com'
    >>> print(cris.preferred_address)
    cris@example.com

A User can also unset their preferred address by setting it to ``None``.

    >>> cris.preferred_address = None
    >>> print(cris.preferred_address)
    None

Addresses
=========

Addresses can be accessed directly:

    >>> address = client.get_address('dana@example.org')
    >>> print(address)
    dana@example.org
    >>> print(address.display_name)
    Dana

The address has not been verified:

    >>> print(address.verified)
    False

But that can be done via the address object:

    >>> address.verify()
    >>> print(address.verified)
    True

It can also be unverified:

    >>> address.unverify()
    >>> print(address.verified)
    False

Addresses can be deleted by calling their ``delete()`` method or by removing
them from their user's ``addresses`` list:

    >>> cris.addresses.remove('dana@example.org')
    >>> for address in cris.addresses:
    ...     print(address)
    cris.person@example.org
    cris@example.com


Users can be added using ``create_user``. The display_name is optional:
    >>> ler = client.create_user(email='ler@primus.org',
    ...                          password='somepass',
    ...                          display_name='Ler')
    >>> print(ler.display_name)
    Ler
    >>> ler = client.get_user('ler@primus.org')
    >>> print(ler.password)
    $...
    >>> print(ler.display_name)
    Ler

User attributes can be changed through assignment, but you need to call the
object's ``save`` method to store the changes in the mailman core database.

    >>> ler.display_name = 'Sir Ler'
    >>> ler.save()
    >>> ler = client.get_user('ler@primus.org')
    >>> print(ler.display_name)
    Sir Ler

Passwords can be changed as well:

    >>> old_pwd = ler.password
    >>> ler.password = 'easy'
    >>> old_pwd == ler.password
    True
    >>> ler.save()
    >>> old_pwd == ler.password
    False


User Subscriptions
------------------

A User's subscriptions can be accessed through the User's ``subscriptions``
property.

    >>> bill = client.get_user('bill@example.com')
    >>> for subscription in bill.subscriptions:
    ...     print(subscription)
    Member "bill@example.com" on "test-1.example.com"

If all you need are the list ids of all mailing lists a user is subscribed to,
you can use the ``subscription_list_ids`` property.

    >>> for list_id in bill.subscription_list_ids:
    ...     print(list_id)
    test-1.example.com


List Settings
=============

We can get all list settings via a lists settings attribute. A proxy object
for the settings is returned which behaves much like a dictionary.

    >>> settings = test_one.settings
    >>> for attr in sorted(settings):
    ...     print(attr + ': ' + str(settings[attr]))
    accept_these_nonmembers: []
    acceptable_aliases: []
    ...
    volume: 1

    >>> print(settings['display_name'])
    Test-1

We can access all valid list settings as attributes.

    >>> print(settings['fqdn_listname'])
    test-1@example.com
    >>> print(settings['description'])
    <BLANKLINE>
    >>> settings['description'] = 'A very meaningful description.'
    >>> settings['display_name'] = 'Test Numero Uno'

    >>> settings.save()

    >>> settings_new = test_one.settings
    >>> print(settings_new['description'])
    A very meaningful description.
    >>> print(settings_new['display_name'])
    Test Numero Uno

The settings object also supports the `get` method of usual Python
dictionaries:

    >>> print(settings_new.get('OhNoIForgotTheKey',
    ...                        'HowGoodIPlacedOneUnderTheDoormat'))
    HowGoodIPlacedOneUnderTheDoormat


Preferences
===========

Preferences can be accessed and set for users, members and addresses.

By default, preferences are not set and fall back to the global system
preferences. They're read-only and can be accessed through the client object.

    >>> global_prefs = client.preferences
    >>> print(global_prefs['acknowledge_posts'])
    False
    >>> print(global_prefs['delivery_mode'])
    regular
    >>> print(global_prefs['delivery_status'])
    enabled
    >>> print(global_prefs['hide_address'])
    True
    >>> print(global_prefs['preferred_language'])
    en
    >>> print(global_prefs['receive_list_copy'])
    True
    >>> print(global_prefs['receive_own_postings'])
    True

Preferences can be set, but you have to call ``save`` to make your changes
permanent.

    >>> prefs = test_two.get_member('anna@example.com').preferences
    >>> prefs['delivery_status'] = 'by_user'
    >>> prefs.save()
    >>> prefs = test_two.get_member('anna@example.com').preferences
    >>> print(prefs['delivery_status'])
    by_user


Pipelines and Chains
====================

The available pipelines and chains can also be retrieved:

    >>> pipelines = client.pipelines['pipelines']
    >>> for pipeline in pipelines:
    ...     print(pipeline)
    default-owner-pipeline
    default-posting-pipeline
    virgin
    >>> chains = client.chains['chains']
    >>> for chain in chains:
    ...     print(chain)
    accept
    default-owner-chain
    default-posting-chain
    discard
    dmarc
    header-match
    hold
    moderation
    reject


Owners and Moderators
=====================

Owners and moderators are properties of the list object.

    >>> test_one.owners
    []
    >>> test_one.moderators
    []

Owners can be added via the ``add_owner`` method and they can have an optional
``display_name`` associated like other ``members``:

    >>> test_one.add_owner('foo@example.com', display_name='Foo')
    >>> for owner in test_one.owners:
    ...     print(owner.email)
    foo@example.com

The owner of the list not automatically added as a member:

    >>> for m in test_one.members:
    ...     print(m)
    Member "bill@example.com" on "test-1.example.com"

Moderators can be added similarly:

    >>> test_one.add_moderator('bar@example.com', display_name='Bar')
    >>> for moderator in test_one.moderators:
    ...     print(moderator.email)
    bar@example.com

Moderators are also not automatically added as members:

    >>> for m in test_one.members:
    ...     print(m)
    Member "bill@example.com" on "test-1.example.com"

Members and owners/moderators are separate entries in the general members
list:

    >>> print(test_one.subscribe('bar@example.com', 'Bar',
    ...                          pre_verified=True,
    ...                          pre_confirmed=True))
    Member "bar@example.com" on "test-1.example.com"

    >>> test_four_net = example_net.create_list('test-4')
    >>> test_four_net.add_owner('foo@example.com', display_name='Foo')
    >>> for member in client.members:
    ...     print('%s: %s' % (member, member.role))
    Member "foo@example.com" on "test-1.example.com": owner
    Member "bar@example.com" on "test-1.example.com": moderator
    Member "bar@example.com" on "test-1.example.com": member
    Member "bill@example.com" on "test-1.example.com": member
    Member "anna@example.com" on "test-2.example.com": member
    Member "foo@example.com" on "test-4.example.net": owner

You can find the lists that a user is a member, moderator, or owner of:

    >>> lists = client.find_lists('bill@example.com', 'member')
    >>> for m_list in lists:
    ...     print(m_list.fqdn_listname)
    test-1@example.com
    >>> lists = client.find_lists('bar@example.com', 'moderator')
    >>> for m_list in lists:
    ...     print(m_list.fqdn_listname)
    test-1@example.com
    >>> lists = client.find_lists('foo@example.com', 'owner')
    >>> for m_list in lists:
    ...     print(m_list.fqdn_listname)
    test-1@example.com
    test-4@example.net

You can also filter those results by domain:

    >>> lists = client.find_lists('foo@example.com', 'owner',
    ...                           mail_host='example.net')
    >>> for m_list in lists:
    ...     print(m_list.fqdn_listname)
    test-4@example.net

Both owners and moderators can be removed:

    >>> test_one.remove_owner('foo@example.com')
    >>> test_one.owners
    []

    test_one.remove_moderator('bar@example.com')
    test_one.moderators
    []


Moderation
==========


Subscription Moderation
-----------------------

Subscription requests can be accessed through the list object's
`request` property. So let's create a non-open list first.

    >>> confirm_first = example_dot_com.create_list('confirm-first')
    >>> settings = confirm_first.settings
    >>> settings['subscription_policy'] = 'confirm_then_moderate'
    >>> settings.save()

    >>> confirm_first = client.get_list('confirm-first.example.com')
    >>> print(confirm_first.settings['subscription_policy'])
    confirm_then_moderate

Initially there are no requests, so let's subscribe someone to the
list. We'll get a token back.

    >>> confirm_first.requests
    []
    >>> data = confirm_first.subscribe('groucho@example.com',
    ...                                pre_verified=True,
    ...                                pre_confirmed=True)
    >>> print(data['token_owner'])
    moderator

Now the request shows up in the list of requests:

    >>> import time; time.sleep(5)
    >>> confirm_first.get_requests_count()
    1

    >>> request_1 = confirm_first.requests[0]
    >>> print(request_1['email'])
    groucho@example.com
    >>> print (request_1['token'] is not None)
    True
    >>> print(request_1['token_owner'])
    moderator
    >>> print(request_1['request_date'] is not None)
    True
    >>> print(request_1['list_id'])
    confirm-first.example.com

It is possible to filter subscription requests based on who is it pending an
action from using ``token_owner`` parameter::

    >>> data = confirm_first.subscribe('harpo@example.com',
    ...                                pre_verified=True,
    ...                                pre_confirmed=True)
    >>> data = confirm_first.subscribe('zeppo@example.com',
    ...                                pre_verified=True,
    ...                                pre_confirmed=False)

    >>> confirm_first.get_requests_count()
    3


Possible values for ``token_owner`` include:
- ``subscriber``
- ``moderator``
- ``no_one``


All these are pending an approval from moderator::

    >>> confirm_first.get_requests_count(token_owner='moderator')
    2

Subscriptions which aren't ``pre_confirmed`` first require confirmation from
the user if list's subscription policy is ``confirm`` or
``confirm_then_moderate``::

    >>> confirm_first.get_requests_count(token_owner='subscriber')
    1
    >>> data = confirm_first.get_requests(token_owner='subscriber')[0]
    >>> print(data['email'])
    zeppo@example.com

Subscription requests can be accepted, deferred, rejected or
discarded using the request token.

Let's accept Groucho:

    >>> response = confirm_first.moderate_request(request_1['token'], 'accept')
    >>> confirm_first.get_requests_count()
    2

    >>> request_2 = confirm_first.requests[0]
    >>> print(request_2['email'])
    harpo@example.com

    >>> request_3 = confirm_first.requests[1]
    >>> print(request_3['email'])
    zeppo@example.com

Let's reject Harpo:

    >>> response = confirm_first.moderate_request(request_2['token'], 'reject')
    >>> confirm_first.get_requests_count()
    1

Let's discard Zeppo's request:

    >>> response = confirm_first.moderate_request(request_3['token'], 'discard')
    >>> confirm_first.get_requests_count()
    0


Message Moderation
------------------

By injecting a message by a non-member into the incoming queue, we can
simulate a message being held for moderator approval.

    >>> msg = """From: nomember@example.com
    ... To: test-1@example.com
    ... Subject: Something
    ... Message-ID: <moderated_01>
    ...
    ... Some text.
    ...
    ... """
    >>> inq = client.queues['in']
    >>> inq.inject('test-1.example.com', msg)

Now wait until the message has been processed.

    >>> while True:
    ...     if len(inq.files) == 0:
    ...         break
    ...     time.sleep(0.1)

It might take a few moments for the message to show up in the moderation
queue.

    >>> while True:
    ...     if test_one.get_held_count() > 0:
    ...         break
    ...     time.sleep(0.1)

Messages held for moderation can be listed on a per list basis.

    >>> all_held = test_one.held
    >>> print(all_held[0].request_id)
    1

A held message can be retrieved by ID, and have attributes:

    >>> heldmsg = test_one.get_held_message(1)
    >>> print(heldmsg.subject)
    Something
    >>> print(heldmsg.reason)
    The message is not from a list member
    >>> print(heldmsg.sender)
    nomember@example.com
    >>> 'Message-ID: <moderated_01>' in heldmsg.msg
    True

A moderation action can be taken on them using the list methods or the held
message's methods.

    >>> print(test_one.defer_message(heldmsg.request_id).status_code)
    204

    >>> len(test_one.held)
    1

    >>> print(heldmsg.discard().status_code)
    204

    >>> len(test_one.held)
    0

Member moderation
-----------------

Each member or non-member can have a specific moderation action. It is set
using the 'moderation_action' property:

    >>> bill_member = test_one.get_member('bill@example.com')
    >>> print(bill_member.moderation_action)
    None
    >>> bill_member.moderation_action = 'hold'
    >>> bill_member.save()
    >>> print(test_one.get_member('bill@example.com').moderation_action)
    hold

Banning addresses
-----------------

A ban list is a list of email addresses that are not allowed to subscribe to a
mailing-list. There are two types of ban lists: each mailing-list has its ban
list, and there is a site-wide list. Addresses on the site-wide list are
prevented from subscribing to every mailing-list on the server.

To view the site-wide ban list, use the `bans` property::

    >>> list(client.bans)
    []

You can use the `add` method on the ban list to ban an email address::

    >>> banned_anna = client.bans.add('anna@example.com')
    >>> print(banned_anna)
    anna@example.com
    >>> 'anna@example.com' in client.bans
    True
    >>> print(client.bans.add('bill@example.com'))
    bill@example.com
    >>> for addr in list(client.bans):
    ...     print(addr)
    anna@example.com
    bill@example.com

The list of banned addresses can be paginated using the ``get_bans_page()``
method::

    >>> for addr in list(client.get_bans_page(count=1, page=1)):
    ...     print(addr)
    anna@example.com
    >>> for addr in list(client.get_bans_page(count=1, page=2)):
    ...     print(addr)
    bill@example.com

You can use the ``delete()`` method on a banned address to unban it, or the
``remove()`` method on the ban list::

    >>> banned_anna.delete()
    >>> 'anna@example.com' in client.bans
    False
    >>> for addr in list(client.bans):
    ...     print(addr)
    bill@example.com
    >>> client.bans.remove('bill@example.com')
    >>> 'bill@example.com' in client.bans
    False
    >>> print(list(client.bans))
    []


The mailing-list-specific ban lists work in the same way::

    >>> print(list(test_one.bans))
    []
    >>> banned_anna = test_one.bans.add('anna@example.com')
    >>> 'anna@example.com' in test_one.bans
    True
    >>> print(test_one.bans.add('bill@example.com'))
    bill@example.com
    >>> for addr in list(test_one.bans):
    ...     print(addr)
    anna@example.com
    bill@example.com
    >>> for addr in list(test_one.get_bans_page(count=1, page=1)):
    ...     print(addr)
    anna@example.com
    >>> for addr in list(test_one.get_bans_page(count=1, page=2)):
    ...     print(addr)
    bill@example.com
    >>> banned_anna.delete()
    >>> 'anna@example.com' in test_one.bans
    False
    >>> test_one.bans.remove('bill@example.com')
    >>> print(list(test_one.bans))
    []


Archivers
=========


Each list object has an ``archivers`` attribute.

    >>> archivers = test_one.archivers
    >>> print(archivers)
    Archivers on test-1.example.com

The activation status of each available archiver can be accessed like a
key in a dictionary.

    >>> archivers = test_one.archivers
    >>> for archiver in sorted(archivers.keys()):
    ...     print('{0}: {1}'.format(archiver, archivers[archiver]))
    mail-archive: True
    mhonarc: True
    prototype: True

    >>> archivers['mail-archive']
    True
    >>> archivers['mhonarc']
    True

They can also be set like items in dictionary.

    >>> archivers['mail-archive'] = False
    >>> archivers['mhonarc'] = False

So if we get a new ``archivers`` object from the API (by accessing the
list's archiver attribute again), we can see that the archiver stati
have now been set.

    >>> archivers = test_one.archivers
    >>> archivers['mail-archive']
    False
    >>> archivers['mhonarc']
    False


Header matches
==============

Header matches are filtering rules that apply to messages sent to a mailing
list. They match a header to a pattern using a regular expression, and matching
patterns can trigger specific moderation actions. They are accessible via the
mailing list's ``header_matches`` attribute, which behaves like a list.

    >>> header_matches = test_one.header_matches
    >>> print(header_matches)
    Header matches for "test-1.example.com"
    >>> len(header_matches)
    0

Header matches can be added using the ``add()`` method. The arguments are:

- the header to consider (``str``). Il will be lower-cased.
- the regular expression to use for filtering (``str``)
- the action to take when the header matches the pattern. This can be
  ``'accept'``, ``'discard'``, ``'reject'``, or ``'hold'``.
- the tag (``str``) to group a set of header matches.

    >>> print(header_matches.add('Subject', '^test: ', 'discard', 'sometag'))
    Header match on "subject"
    >>> print(header_matches)
    Header matches for "test-1.example.com"
    >>> len(header_matches)
    1
    >>> for hm in list(header_matches):
    ...     print(hm)
    Header match on "subject"

Header matches can be filtered using ``.find()`` method to query a set
of HeaderMatches::

  >>> header_matches.find(tag='sometag')
  [<HeaderMatch on 'subject'>]

You can delete a header match by deleting it from the ``header_matches``
collection.

    >>> del header_matches[0]
    >>> len(header_matches)
    0

You can also delete a header match using its ``delete()`` method, but be aware
that the collection will not automatically be updated. Get a new collection
from the list's ``header_matches`` attribute to see the change.

    >>> print(header_matches.add('Subject', '^test: ', 'discard'))
    Header match on "subject"
    >>> header_matches[0].delete()
    >>> len(header_matches) # not automatically updated
    1
    >>> len(test_one.header_matches)
    0


Configuration
=============

Mailman Core exposes all its configuration through REST API. All these
configuration options are read-only.

    >>> cfg = client.configuration
    >>> for key in sorted(cfg):
    ...     print(cfg[key].name)
    ARC
    antispam
    archiver.mail_archive
    archiver.master
    archiver.mhonarc
    archiver.prototype
    bounces
    database
    devmode
    digests
    dmarc
    language.ar
    language.ast
    language.ca
    language.cs
    language.da
    language.de
    language.el
    language.en
    language.es
    language.et
    language.eu
    language.fi
    language.fr
    language.gl
    language.he
    language.hr
    language.hu
    language.ia
    language.it
    language.ja
    language.ko
    language.lt
    language.nl
    language.no
    language.pl
    language.pt
    language.pt_BR
    language.ro
    language.ru
    language.sk
    language.sl
    language.sr
    language.sv
    language.tr
    language.uk
    language.vi
    language.zh_CN
    language.zh_TW
    logging.archiver
    logging.bounce
    logging.config
    logging.database
    logging.debug
    logging.error
    logging.fromusenet
    logging.http
    logging.locks
    logging.mischief
    logging.plugins
    logging.root
    logging.runner
    logging.smtp
    logging.subscribe
    logging.vette
    mailman
    mta
    nntp
    passwords
    paths.dev
    paths.fhs
    paths.here
    paths.local
    plugin.master
    runner.archive
    runner.bad
    runner.bounces
    runner.command
    runner.digest
    runner.in
    runner.lmtp
    runner.nntp
    runner.out
    runner.pipeline
    runner.rest
    runner.retry
    runner.shunt
    runner.virgin
    shell
    styles
    webservice


Each configuration object is a dictionary and you can iterate over them
::

     >>> for key in sorted(cfg['mailman']):
     ...     print('{} : {}'.format(key, cfg['mailman'][key]))
     cache_life : 7d
     check_max_size_on_filtered_message : no
     default_language : en
     email_commands_max_lines : 10
     filter_report : no
     filtered_messages_are_preservable : no
     hold_digest : no
     html_to_plain_text_command : /usr/bin/lynx -dump $filename
     layout : here
     listname_chars : [-_.0-9a-z]
     masthead_threshold : 4
     noreply_address : noreply
     pending_request_life : 3d
     post_hook :
     pre_hook :
     self_link : http://localhost:9001/3.1/system/configuration/mailman
     sender_headers : from from_ reply-to sender
     site_owner : changeme@example.com

..   >>> for domain in client.domains:
     ...    domain.delete()
     >>> for user in client.users:
     ...    user.delete()

.. _`Core REST API docs`: https://docs.mailman3.org/projects/mailman/en/latest/src/mailman/rest/docs/rest.html
