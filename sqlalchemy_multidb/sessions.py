"""Session objects."""

from sqlalchemy import orm


class Session(orm.Session):
    """Provides support to context."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
