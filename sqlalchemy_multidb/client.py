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


from sqlalchemy_multidb.databases import create_database
from sqlalchemy_multidb.exceptions import DatabaseAlreadyExists
from sqlalchemy_multidb.exceptions import DatabaseNotFound


class SQLAlchemy(object):
    def __init__(self):
        self.__databases = {}

    def config_from_object(self, config):
        dbs = getattr(config, 'DATABASES', None)

        if dbs:
            for name, url in dbs.items():
                self.add_database(name, url)

    def add_database(self, name, url):
        if name is None:
            name = 'default'

        if name in self.__databases:
            raise DatabaseAlreadyExists(name)

        self.__databases[name] = create_database(url)

    def get_database(self, name=None):
        """
        :param name:
        :return: asdasd
        """
        if name is None:
            name = 'default'

        database = self.__databases.get(name)

        if database:
            return database

        raise DatabaseNotFound(name)

    def remove_database(self, name=None):
        if name is None:
            name = 'default'

        engine = self.__databases.pop(name, None)

        if engine:
            engine.close()

        raise DatabaseNotFound(name)

    def session(self, database_name=None, scoped=False):
        if database_name is None:
            database_name = 'default'

        database = self.__databases.get(database_name)

        if database:
            return database.session(scoped=scoped)

        raise DatabaseNotFound(database_name)

    def close(self):
        for database in self.__databases.values():
            database.close()
        self.__databases.clear()
