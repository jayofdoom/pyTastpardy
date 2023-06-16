import uuid

from sqlalchemy import func

from tastpardy.db import DBClient
from tastpardy.models import Question


class Game(object):
    def __init__(self, dbpath=None):
        self.id = uuid.uuid4()
        if dbpath:
            self.session = DBClient(path=dbpath).get_session()
        else:
            self.session = DBClient().get_session()
    
    def single_question(self):
        question = self.session.query(Question).order_by(func.random()).limit(1).one()
        return question


