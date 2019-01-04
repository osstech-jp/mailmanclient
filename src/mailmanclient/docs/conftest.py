# Copyright (C) 2017-2019 by the Free Software Foundation, Inc.
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

"""Wrappers for doctests to run with pytest"""

from __future__ import absolute_import, print_function, unicode_literals

import pytest

from mailmanclient.testing.documentation import dump


def pytest_collection_modifyitems(items):
    for item in items:
        item.add_marker(pytest.mark.vcr)


@pytest.fixture(autouse=True)
def import_stuff(doctest_namespace):
    doctest_namespace['absolute_import'] = absolute_import
    doctest_namespace['print_function'] = print_function
    doctest_namespace['unicode_literals'] = unicode_literals
    doctest_namespace['dump'] = dump
