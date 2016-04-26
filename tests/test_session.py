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

    def test_commit(self):
        class Foo(self.db.Model):
            __tablename__ = 'foo'
            id = Column(Integer, primary_key=True)
            name = Column(String)

        with self.db.session() as session:
            session.execute('create table foo(id int primary key, name text);')
            session.execute("insert into foo values(1, 'foo')")

            foo = session.query(Foo).first()
            foo.name = 'foo2'
            session.commit()
            foo = session.query(Foo).first()

        self.assertEqual('foo2', foo.name)

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
