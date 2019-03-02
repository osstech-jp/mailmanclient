# Copyright (C) 2010-2019 by the Free Software Foundation, Inc.
#
# This file is part of mailman.client.
#
# mailman.client is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# mailman.client is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with mailman.client.  If not, see <http://www.gnu.org/licenses/>.

from setup_helpers import get_version, require_python
from setuptools import setup, find_packages


require_python(0x30500f0)
__version__ = get_version('src/mailmanclient/constants.py')


def readme():
    with open('README.rst') as fd:
        return fd.read()


setup(
    name='mailmanclient',
    version=__version__,
    packages=find_packages('src'),
    description='mailmanclient -- Python bindings for Mailman REST API',
    long_description=readme(),
    long_description_content_type='text/x-rst',
    package_dir={'': 'src'},
    include_package_data=True,
    maintainer='Barry Warsaw',
    maintainer_email='barry@list.org',
    license='LGPLv3',
    url='http://www.list.org/',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)', # noqa
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP ',
    ],
    install_requires=[
        'requests',
        ],
    extras_require={
        'testing': [
            'pytest',
            'pytest-vcr',
            'pytest-services',
            'mailman',
            'falcon==1.4.1',
            ],
        'lint': [
            'flake8>3.0'
           ]
        },
    )
