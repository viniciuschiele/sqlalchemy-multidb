from sqlalchemy_multidb import DatabaseManager


class Config(object):
    DATABASES = {
        'db1': 'sqlite://',
        'db2': 'sqlite://'
    }

db = DatabaseManager()
db.config_from_object(Config())

with db.scoped_session('db1') as session:
    session.scalar('SELECT 1')

with db.scoped_session('db2') as session:
    session.scalar('SELECT 1')
