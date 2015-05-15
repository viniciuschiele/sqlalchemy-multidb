from unittest import TestCase
from sqlalchemy_multidb import SQLAlchemy


class Config(object):
    DATABASES = {
        'default': 'postgresql://postgres:postgres@localhost/postgres'
    }


class TestSession(TestCase):
    def setUp(self):
        self.db = SQLAlchemy()
        self.db.config_from_object(Config())

    def tearDown(self):
        self.db.close()

    def test_instances(self):
        session1 = self.db.session()
        session2 = self.db.session()

        self.assertNotEqual(session1, session2)

    def test_scoped_instances(self):
        session1 = self.db.session(scoped=True)
        session2 = self.db.session(scoped=True)

        self.assertEqual(session1, session2)
