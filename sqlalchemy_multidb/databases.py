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

import sqlalchemy

from sqlalchemy.engine.url import make_url
from sqlalchemy.event import listen
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm.session import sessionmaker
from sqlalchemy_multidb.sessions import Session
from sqlalchemy_multidb.util import ref_to_obj

ENGINE_ALIASES = {
    'postgresql': 'sqlalchemy_multidb.databases:PostgresDatabase',
}


def create_database(url):
    uri = make_url(url)

    class_name = ENGINE_ALIASES.get(uri.drivername)

    if class_name is None:
        return Database(url)

    engine_cls = ref_to_obj(class_name)
    return engine_cls(url)


class Database(object):
    def __init__(self, url):
        self.__url = url
        self.__session_factories = {}
        self.__engine = sqlalchemy.create_engine(url)

    @property
    def engine(self):
        return self.__engine

    def close(self):
        for session_factory in self.__session_factories.values():
            session_factory.close_all()
        self.__session_factories.clear()

        self.__engine.dispose()
        self.__engine = None

    def session(self, database=None, scoped=False):
        return self.__session_factory(database=database, scoped=scoped)()

    def __session_factory(self, **kwargs):
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
    def __init__(self, url):
        url, self.__search_path = self.__pop_search_path(url)

        super().__init__(url)

        if self.__search_path:
            listen(self.engine, 'connect', self.__on_connect)

    def __on_connect(self, dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute('SET search_path TO ' + self.__search_path)
        cursor.close()

    @staticmethod
    def __pop_search_path(url):
        uri = make_url(url)
        search_path = uri.query.pop('search_path', None)
        return str(uri), search_path
