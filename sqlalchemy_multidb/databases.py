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
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy_multidb.exceptions import DatabaseAlreadyExists
from sqlalchemy_multidb.exceptions import DatabaseNotFound
from sqlalchemy_multidb.sessions import Session
from sqlalchemy_multidb.util import import_string

DATABASE_ALIASES = {
    'postgresql': 'sqlalchemy_multidb.databases.PostgresDatabase',
}


class DatabaseManager(object):
    """Provides a container of databases."""

    def __init__(self):
        self.__databases = {}
        self.Model = declarative_base()

    def config_from_object(self, config):
        """Loads the databases from the config."""

        dbs = getattr(config, 'SQLALCHEMY_DATABASES', None)

        if not dbs:
            dbs = getattr(config, 'DATABASES', None)

        if dbs:
            for name, url in dbs.items():
                self.add_database(name, url)

    def close(self):
        """Closes all databases."""

        for database in self.__databases.values():
            database.close()
        self.__databases.clear()

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

    def scoped_session(self, database_name=None):
        """Gets a scoped session for the specified database."""

        database_name = database_name or 'default'

        database = self.__databases.get(database_name)

        if database:
            return database.scoped_session()

        raise DatabaseNotFound(database_name)

    def session(self, database_name=None):
        """Gets a new session for the specified database."""

        database_name = database_name or 'default'

        database = self.__databases.get(database_name)

        if database:
            return database.session()

        raise DatabaseNotFound(database_name)

    @staticmethod
    def __create_database(name, url):
        """Creates a new database from the url."""

        uri = make_url(url)

        class_name = DATABASE_ALIASES.get(uri.drivername)

        if class_name is None:
            return Database(name, url)

        database_cls = import_string(class_name)
        return database_cls(name, url)


class Database(object):
    """Provides methods to get sessions for a specific engine."""

    def __init__(self, name, url):
        self.__name = name
        self.__url, engine_params = self.__parse_url(url)
        self.__engine = sqlalchemy.create_engine(self.__url, **engine_params)
        self.__session_factory = sessionmaker(self.engine, class_=Session, expire_on_commit=False)
        self.__scoped_session_factory = scoped_session(self.__session_factory)
        self.Model = declarative_base()

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

        self.__session_factory.close_all()
        self.__session_factory = None

        self.__scoped_session_factory = None

        self.__engine.dispose()
        self.__engine = None

    def scoped_session(self):
        """Gets a scoped session for the specified database."""
        return self.__scoped_session_factory()

    def session(self):
        """Gets a new session for the specified database."""
        return self.__session_factory()

    @staticmethod
    def __parse_url(url):
        """Gets the parameters from the url."""

        params_keys = {
            'case_sensitive': bool,
            'convert_unicode': bool,
            'echo': bool,
            'echo_pool': bool,
            'encoding': str,
            'isolation_level': str,
            'module': str,
            'pool_reset_on_return': str,
            'strategy': str,
            'paramstyle': str,
            'logging_name': str,
            'pool_logging_name': str,
            'max_overflow': int,
            'pool_size': int,
            'pool_recycle': int,
            'pool_timeout': int,
            'label_length': int,
        }

        uri = make_url(url)

        kwargs = {'connect_args': {}}

        for key, value in uri.query.items():
            param_type = params_keys.get(key)

            if param_type:
                kwargs[key] = param_type(value)
            else:
                kwargs['connect_args'][key] = value

        uri.query.clear()

        return str(uri), kwargs


class PostgresDatabase(Database):
    """
    Postgresql implementation.
    Provides support to search_path from the url.
    """

    def __init__(self, name, url):
        uri = make_url(url)
        self.__search_path = uri.query.pop('search_path', None)

        super().__init__(name, str(uri))

        if self.__search_path:
            listen(self.engine, 'checkout', self.__on_checkout)

    def __on_checkout(self, dbapi_connection, connection_record, connection_proxy):
        """Called when a new connection is open."""

        cursor = dbapi_connection.cursor()
        cursor.execute('SET search_path TO ' + self.__search_path)
        cursor.close()
