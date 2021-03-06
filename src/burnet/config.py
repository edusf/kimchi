#
# Project Burnet
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Anthony Liguori <aliguori@us.ibm.com>
#  Adam Litke <agl@linux.vnet.ibm.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#

import os, os.path
from glob import iglob
import sys
from distutils.dist import Distribution
import platform

d = Distribution()
d.parse_config_files()
opt = d.get_option_dict('install').get('prefix')
PREFIX = opt[1] if opt is not None else sys.prefix


def get_prefix():
    if __file__[0] == '/':
        base = os.path.dirname(__file__)
    else:
        base = os.path.dirname('./%s' % __file__)

    if os.access('%s/../../src/burnet/config.py' % base, os.F_OK):
        return '%s/../..' % base
    else:
        return '%s/share/burnet' % PREFIX

def get_default_log_dir():
    prefix = get_prefix()

    if prefix.endswith("/share/burnet"):
        return "/var/log/burnet"

    return os.path.join(prefix, 'log')

def get_object_store():
    return os.path.join(get_prefix(), 'data', 'objectstore')

def get_template_path(resource):
    return '%s/ui/pages/%s.tmpl' % (get_prefix(), resource)

def get_screenshot_path():
    return "%s/data/screenshots" % get_prefix()

def get_mo_path():
    return '%s/i18n/mo' % get_prefix()

def get_support_language():
    mopath = "%s/*" % get_mo_path()
    return [path.rsplit('/', 1)[1] for path in iglob(mopath)]

def find_qemu_binary():
    locations = ['/usr/bin/qemu-system-%s' % platform.machine(),
                    '/usr/libexec/qemu-kvm']
    for location in locations:
        if os.path.exists(location):
            return location
    raise Exception("Unable to locate qemu binary")


if __name__ == '__main__':
    print get_prefix()
