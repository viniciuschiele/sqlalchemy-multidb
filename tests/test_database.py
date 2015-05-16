# Copyright 2015 Vinicius Chiele. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for database object."""

from unittest import TestCase
from sqlalchemy_multidb import DatabaseManager
from sqlalchemy_multidb.databases import Database
from sqlalchemy_multidb.exceptions import DatabaseAlreadyExists
from sqlalchemy_multidb.exceptions import DatabaseNotFound


class TestSession(TestCase):
    def setUp(self):
        self.db = DatabaseManager()

    def tearDown(self):
        self.db.close()

    def test_default(self):
        self.db.add_database(None, 'sqlite://')

        db = self.db.get_database()
        self.assertIsInstance(db, Database)
        self.assertEqual(db.name, 'default')
        self.assertNotEqual(db.engine, None)

        self.db.remove_database()
        self.assertRaises(DatabaseNotFound, self.db.get_database)

    def test_already_exists(self):
        self.db.add_database('db1', 'sqlite://')
        self.assertRaises(DatabaseAlreadyExists, self.db.add_database, 'db1', 'sqlite://')

    def test_not_found(self):
        self.assertRaises(DatabaseNotFound, self.db.get_database, 'unknown')
