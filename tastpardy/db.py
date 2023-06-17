from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlite3 import Connection

from tastpardy.models import Base


class DBClient(object):
    def __init__(self, path: str = "../data.db", echo: bool = False):
        sqlite_path = f"sqlite:///{path}"
        self.engine = create_engine(sqlite_path, echo=echo)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.session

    def get_engine(self):
        return self.engine


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection: Connection, _):  # type: ignore
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()
