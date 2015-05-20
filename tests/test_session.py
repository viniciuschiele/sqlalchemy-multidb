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

"""Unit tests for session object."""

from unittest import TestCase
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy_multidb import DatabaseManager


class Config(object):
    DATABASES = {
        'default': 'sqlite://'
    }


class TestSession(TestCase):
    def setUp(self):
        self.db = DatabaseManager()
        self.db.config_from_object(Config())

    def tearDown(self):
        self.db.close()

    def test_instances(self):
        session1 = self.db.session()
        session2 = self.db.session()

        self.assertNotEqual(session1, session2)

    def test_scoped_instances(self):
        session1 = self.db.scoped_session()
        session2 = self.db.scoped_session()

        self.assertEqual(session1, session2)

    def test_model_out_of_context(self):
        class Foo(self.db.Model):
            __tablename__ = 'foo'
            id = Column(Integer, primary_key=True)
            name = Column(String)

        with self.db.session() as session:
            session.execute('create table foo(id int primary key, name text);')
            session.execute("insert into foo values(1, 'foo')")
            foo = session.query(Foo).first()

        self.assertEqual(1, foo.id)
