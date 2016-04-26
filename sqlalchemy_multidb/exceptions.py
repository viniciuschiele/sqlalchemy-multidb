"""This module contains all exceptions used."""


class DatabaseAlreadyExists(Exception):
    """Database exists in the DatabaseManager."""

    def __init__(self, database):
        super(DatabaseAlreadyExists, self).__init__("Database '%s' already exists." % database)


class DatabaseNotFound(Exception):
    """Database not found in the DatabaseManager."""

    def __init__(self, database):
        super(DatabaseNotFound, self).__init__("Database '%s' not found." % database)
