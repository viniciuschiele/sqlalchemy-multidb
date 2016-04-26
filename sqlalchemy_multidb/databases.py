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
from .exceptions import DatabaseAlreadyExists, DatabaseNotFound
from .sessions import Session
from .util import import_string


DATABASE_ALIASES = {
    'postgresql': 'sqlalchemy_multidb.databases.PostgresDatabase',
}


class DatabaseManager(object):
    """
    Provides a container of databases.
    :param scope_func: optional function which defines the current scope.
    """
    def __init__(self, scope_func=None):
        self._databases = {}
        self._scope_func = scope_func
        self.Model = declarative_base()

    @property
    def databases(self):
        """
        Gets the databases.
        :return: The list with all databases.
        """
        return self._databases.values()

    def config_from_object(self, config):
        """
        Loads the databases from the config.
        :param config: The object containing the database config.
        """
        dbs = getattr(config, 'SQLALCHEMY_DATABASES', None)

        if not dbs:
            dbs = getattr(config, 'DATABASES', None)

        if dbs:
            for name, url in dbs.items():
                self.add_database(name, url)

    def close(self):
        """
        Closes all databases.
        """

        for database in self._databases.values():
            database.close()

        self._databases.clear()

    def add_database(self, name, url):
        """
        Adds a new database from the url.
        :param name: The name of the database.
        :param url: The connection string.
        """
        name = name or 'default'

        if not isinstance(name, str):
            raise TypeError('Parameter name should be a str.')

        if not isinstance(url, str):
            raise TypeError('Parameter url should be a str.')

        if name in self._databases:
            raise DatabaseAlreadyExists(name)

        self._databases[name] = self._create_database(name, url)

    def get_database(self, name=None):
        """
        Gets a database by the name.
        :param name: The database name.
        """
        name = name or 'default'

        database = self._databases.get(name)

        if database:
            return database

        raise DatabaseNotFound(name)

    def remove_database(self, name=None):
        """
        Removes a database by the name.
        :param name: The database name.
        """
        name = name or 'default'

        database = self._databases.pop(name, None)

        if not database:
            raise DatabaseNotFound(name)

        database.close()

    def session(self, database_name=None):
        """
        Gets a new session for the specified database.
        :param database_name: The database name.
        :return: The new session.
        """
        database_name = database_name or 'default'

        database = self._databases.get(database_name)

        if database:
            return database.session()

        raise DatabaseNotFound(database_name)

    def scoped_session(self, database_name=None):
        """
        Gets a new scoped session for the specified database.
        :param database_name: The database name.
        :return: The new scoped session.
        """
        database_name = database_name or 'default'

        database = self._databases.get(database_name)

        if database:
            return database.scoped_session()

        raise DatabaseNotFound(database_name)

    def _create_database(self, name, url):
        """
        Creates a new database from the url.
        :param name: The database name.
        :param url: The connection string.
        :return: A new instance of `Database`.
        """
        uri = make_url(url)

        class_name = DATABASE_ALIASES.get(uri.drivername)

        if class_name is None:
            database_cls = Database
        else:
            database_cls = import_string(class_name)

        return database_cls(name, url, scope_func=self._scope_func)


class Database(object):
    """
    Provides methods to get sessions for a specific engine.
    """

    def __init__(self, name, url, scope_func):
        self._name = name
        self._url, engine_params = self._parse_url(url)
        self._engine = sqlalchemy.create_engine(self._url, **engine_params)
        self._session_maker = sessionmaker(self.engine, class_=Session, expire_on_commit=False)
        self._scoped_session_maker = scoped_session(self._session_maker, scopefunc=scope_func)
        self.Model = declarative_base()

    @property
    def name(self):
        """
        Gets the database name.
        """
        return self._name

    @property
    def engine(self):
        """
        Gets the database engine.
        """
        return self._engine

    @property
    def session_maker(self):
        """
        Gets the session maker.
        """
        return self._session_maker

    @property
    def scoped_session_maker(self):
        """
        Gets the scoped session maker.
        """
        return self._scoped_session_maker

    def close(self):
        """
        Closes the engine and all its sessions opened.
        """
        self._session_maker.close_all()
        self._session_maker = None

        self._scoped_session_maker = None

        self._engine.dispose()
        self._engine = None

    def session(self):
        """
        Gets a new session for the specified database.
        """
        return self._session_maker()

    def scoped_session(self):
        """
        Gets a scoped session for the specified database.
        """
        return self._scoped_session_maker()

    @staticmethod
    def _parse_url(url):
        """
        Gets the parameters from the url.
        """

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
    PostgreSQL implementation.
    Provides support to search_path from the url.
    """

    def __init__(self, name, url, scope_func=None):
        uri = make_url(url)
        self.__search_path = uri.query.pop('search_path', None)

        super(PostgresDatabase, self).__init__(name, str(uri), scope_func)

        if self.__search_path:
            listen(self.engine, 'checkout', self.__on_checkout)

    def __on_checkout(self, dbapi_connection, connection_record, connection_proxy):
        """Called when a new connection is open."""

        cursor = dbapi_connection.cursor()
        cursor.execute('SET search_path TO ' + self.__search_path)
        cursor.close()
