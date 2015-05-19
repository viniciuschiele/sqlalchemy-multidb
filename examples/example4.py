from sqlalchemy_multidb import DatabaseManager


class Config(object):
    DATABASES = {
        'db1': 'sqlite://',
        'db2': 'sqlite://'
    }

dbm = DatabaseManager()
dbm.config_from_object(Config())

db = dbm.get_database('db1')

with db.session() as session:
    session.scalar('SELECT 1')
