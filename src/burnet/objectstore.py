# Project Kimchi
#
# Copyright IBM, Corp. 2013
#
# Authors:
#  Shu Ming <shuming@linux.vnet.ibm.com>
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

import json
import threading
import sqlite3
from collections import OrderedDict
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict
import config
import burnet.model


class ObjectStoreSession(object):
    def __init__(self, conn):
        self.conn = conn

    def get_list(self, obj_type):
        c = self.conn.cursor()
        res = c.execute('SELECT id FROM objects WHERE type=?', (obj_type,))
        return [x[0] for x in res]

    def get(self, obj_type, ident):
        c = self.conn.cursor()
        res = c.execute('SELECT json FROM objects WHERE type=? AND id=?',
                        (obj_type, ident))
        try:
            jsonstr = res.fetchall()[0][0]
        except IndexError:
            self.conn.rollback()
            raise burnet.model.NotFoundError(ident)
        return json.loads(jsonstr)

    def delete(self, obj_type, ident):
        c = self.conn.cursor()
        c.execute('DELETE FROM objects WHERE type=? AND id=?',
                  (obj_type, ident))
        if c.rowcount != 1:
            self.conn.rollback()
            raise burnet.model.NotFoundError(ident)
        self.conn.commit()

    def store(self, obj_type, ident, data):
        jsonstr = json.dumps(data)
        c = self.conn.cursor()
        c.execute('DELETE FROM objects WHERE type=? AND id=?',
                  (obj_type, ident))
        c.execute('INSERT INTO objects (id, type, json) VALUES (?,?,?)',
                  (ident, obj_type, jsonstr))
        self.conn.commit()


class ObjectStore(object):
    def __init__(self, location=None):
        self._lock = threading.Semaphore()
        self._connections = OrderedDict()
        self.location = location or config.get_object_store()
        with self._lock:
            self._init_db()

    def _init_db(self):
        conn = self._get_conn()
        c = conn.cursor()
        c.execute('''SELECT * FROM sqlite_master WHERE type='table' AND
                     tbl_name='objects'; ''')
        res = c.fetchall()
        # Because the tasks are regarded as temporary resource, the task states
        # are purged every time the daemon startup
        if len(res) == 0:
            c.execute('''CREATE TABLE objects
                (id TEXT, type TEXT, json TEXT, PRIMARY KEY (id, type))''')
            conn.commit()
            return

        # Clear out expired objects from a previous session
        c.execute('''DELETE FROM objects WHERE type = 'task'; ''')
        conn.commit()

    def _get_conn(self):
        ident = threading.currentThread().ident
        try:
            return self._connections[ident]
        except KeyError:
            self._connections[ident] = sqlite3.connect(self.location, timeout=10)
            if len(self._connections.keys()) > 10:
                id, conn = self._connections.popitem(last=False)
                conn.interrupt()
                del conn
            return self._connections[ident]

    def __enter__(self):
        self._lock.acquire()
        return ObjectStoreSession(self._get_conn())

    def __exit__(self, type, value, tb):
        self._lock.release()
