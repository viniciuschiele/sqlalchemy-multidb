from sqlalchemy_multidb import DatabaseManager

db = DatabaseManager()
db.add_database('default', 'sqlite://')

with db.session() as session:
    session.scalar('SELECT 1')