import abc
from dataclasses import dataclass
import uuid

from sqlalchemy import func

from tastpardy.db import DBClient
from tastpardy.models import Question


@dataclass
class ChannelStats:
    members: list[str]|None
    topic: str|None
    name: str|None


class GameRunner(abc.ABC):
    @abc.abstractmethod
    def message(self, message: list[str], target: str):
        """Send one or more messages to the public channel.

        Messages sent by this should be sent as fast as the backend allows.

        :param message: A string or list of strings to send to the public channel.
        """
        pass

    @abc.abstractmethod
    def wait(self, seconds: int | float):
        """Wait for a specified number of seconds.

        Implementations can wait for a longer period of time if needed.

        :param seconds: The number of seconds to wait.
        """
        pass
    
    @abc.abstractmethod
    def channel_stats(self) -> ChannelStats:
        """Returns information about the public channel attached to the runner."""
        pass


class Game(object):
    def __init__(self, runner: GameRunner, dbpath: str | None = None):
        self.id = uuid.uuid4()
        self.runner = runner

        if dbpath:
            self.session = DBClient(path=dbpath).get_session()
        else:
            self.session = DBClient().get_session()

    def single_question(self, target: str):
        """Returns a list of actions to perform the requested game action."""
        question = self.session.query(Question).order_by(func.random()).limit(1).one()

        self.runner.message(
            [
                "Let's play Tastpardy! Only one question for now. "
                "You'll get 30 seconds to think, then I'll give you the answer!",
                "-------------------",
                "Air Date: {}. Difficulty: {}. Category: {}".format(
                    question.aired, question.difficulty, question.category.name
                ),
                "-------------------",
                str(question.question),
            ],
            target,
        )
        self.runner.wait(30)
        self.runner.message(
            [
                "The answer was: What is {}? I hope you got it right!".format(
                    question.answer
                )
            ],
            target,
        )
