from sqlalchemy_multidb import DatabaseManager

db = DatabaseManager()
db.add_database('db1', 'sqlite://')
db.add_database('db2', 'sqlite://')

with db.session('db1') as session:
    session.scalar('SELECT 1')

with db.session('db2') as session:
    session.scalar('SELECT 1')
