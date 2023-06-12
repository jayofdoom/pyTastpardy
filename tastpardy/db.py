from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from tastpardy.models import Base


class DBClient(object):
    def __init__(self, path='data.db', echo=False):
        self.engine = create_engine('sqlite:///data.db', echo=echo)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        Base.metadata.create_all(self.engine)

    def get_session(self):
        return self.session

    def get_engine(self):
        return self.engine


@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()