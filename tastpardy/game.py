import ssl
import time
import uuid

from sqlalchemy import func
import irc.bot  # type: ignore
import irc.connection  # type: ignore
import irc.strings  # type: ignore

from tastpardy.config import IRCConfig
from tastpardy.db import DBClient
from tastpardy.models import Question


class Game(object):
    def __init__(self):
        self.id = uuid.uuid4()
        self.session = DBClient().get_session()
    
    def single_question(self):
        question = self.session.query(Question).order_by(func.random()).limit(1).one()
        return question


