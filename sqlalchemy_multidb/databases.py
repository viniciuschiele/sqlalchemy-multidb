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

"""Database objects."""

import sqlalchemy

from sqlalchemy.engine.url import make_url
from sqlalchemy.event import listen
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy_multidb.exceptions import DatabaseAlreadyExists
from sqlalchemy_multidb.exceptions import DatabaseNotFound
from sqlalchemy_multidb.sessions import Session
from sqlalchemy_multidb.util import ref_to_obj


DATABASE_ALIASES = {
    'postgresql': 'sqlalchemy_multidb.databases:PostgresDatabase',
}


class DatabaseManager(object):
    """Provides a container of databases."""

    def __init__(self):
        self.__databases = {}

    def config_from_object(self, config):
        """Loads the databases from the config."""

        dbs = getattr(config, 'DATABASES', None)

        if dbs:
            for name, url in dbs.items():
                self.add_database(name, url)

    def add_database(self, name, url):
        """Adds a new database from the url."""

        name = name or 'default'

        if not isinstance(name, str):
            raise TypeError('Parameter name should be a str.')

        if not isinstance(url, str):
            raise TypeError('Parameter url should be a str.')

        if name in self.__databases:
            raise DatabaseAlreadyExists(name)

        self.__databases[name] = self.__create_database(name, url)

    def get_database(self, name=None):
        """Gets a database by the name."""

        name = name or 'default'

        database = self.__databases.get(name)

        if database:
            return database

        raise DatabaseNotFound(name)

    def remove_database(self, name=None):
        """Removes a database by the name."""

        name = name or 'default'

        database = self.__databases.pop(name, None)

        if not database:
            raise DatabaseNotFound(name)

        database.close()

    def session(self, database_name=None, scoped=False):
        """Gets a new session for the specified database."""

        database_name = database_name or 'default'

        database = self.__databases.get(database_name)

        if database:
            return database.session(scoped=scoped)

        raise DatabaseNotFound(database_name)

    def close(self):
        """Closes all databases."""

        for database in self.__databases.values():
            database.close()
        self.__databases.clear()

    @staticmethod
    def __create_database(name, url):
        """Creates a new database from the url."""

        uri = make_url(url)

        class_name = DATABASE_ALIASES.get(uri.drivername)

        if class_name is None:
            return Database(name, url)

        database_cls = ref_to_obj(class_name)
        return database_cls(name, url)


class Database(object):
    """Provides methods to get sessions for a specific engine."""

    def __init__(self, name, url):
        self.__name = name
        self.__url = url
        self.__session_factories = {}
        self.__engine = sqlalchemy.create_engine(url)

    @property
    def name(self):
        """Gets the name."""
        return self.__name

    @property
    def engine(self):
        """Gets the engine."""
        return self.__engine

    def close(self):
        """Closes the engine and all sessions opened."""

        for session_factory in self.__session_factories.values():
            session_factory.close_all()
        self.__session_factories.clear()

        self.__engine.dispose()
        self.__engine = None

    def session(self, scoped=False):
        """Gets a new session for the specified database."""
        return self.__session_factory(scoped=scoped)()

    def __session_factory(self, **kwargs):
        """Gets a session maker."""

        key = hash(frozenset(kwargs.items()))

        session_factory = self.__session_factories.get(key)

        if not session_factory:
            session_factory = sessionmaker(self.engine, class_=Session)

            scoped = kwargs.get('scoped', False)
            if scoped:
                session_factory = scoped_session(session_factory)
            self.__session_factories[key] = session_factory

        return session_factory


class PostgresDatabase(Database):
    """
    Postgresql implementation.
    Provides support to search_path from the url.
    """

    def __init__(self, name, url):
        url, self.__search_path = self.__pop_search_path(url)

        super().__init__(name, url)

        if self.__search_path:
            listen(self.engine, 'connect', self.__on_connect)

    def __on_connect(self, dbapi_connection, connection_record):
        """Called when a new connection is open."""

        cursor = dbapi_connection.cursor()
        cursor.execute('SET search_path TO ' + self.__search_path)
        cursor.close()

    @staticmethod
    def __pop_search_path(url):
        """Gets the parameter search_path from the url."""

        uri = make_url(url)
        search_path = uri.query.pop('search_path', None)
        return str(uri), search_path
