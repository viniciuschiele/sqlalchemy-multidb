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
