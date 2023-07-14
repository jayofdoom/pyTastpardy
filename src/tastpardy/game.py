import abc
from dataclasses import dataclass
from thefuzz import fuzz, utils
from typing import Callable
import uuid

from sqlalchemy import func

from tastpardy.db import DBClient
from tastpardy.models import Question


@dataclass
class ChannelStats:
    members: list[str] | None
    topic: str | None
    name: str | None


@dataclass
class Response:
    nick: str
    message: str
    accuracy: int

    def __str__(self):
        return f"{self.nick} answered {self.message}, which was {self.accuracy}% correct."


class GameRunner(abc.ABC):
    @abc.abstractmethod
    def message(self, message: list[str], target: str):
        """Send one or more messages to the public channel.

        Messages sent by this should be sent as fast as the backend allows.

        :param message: A string or list of strings to send to the public channel.
        """
        pass

    @abc.abstractmethod
    def wait(self, seconds: int | float) -> None:
        """Wait for a specified number of seconds.

        Implementations can wait for a longer period of time if needed.

        :param seconds: The number of seconds to wait.
        """
        pass

    @abc.abstractmethod
    def channel_stats(self) -> ChannelStats:
        """Returns information about public channel attached to the runner."""
        pass

    @abc.abstractmethod
    def listen_for_messages(self, callback: Callable[[str, str, str], None]) -> str:
        """Run a method for each message recieved until aborted.

        Implementations are expected to call the callback with every message
        receieved in the channel until the listener is aborted. Implementations
        must return a uniquely identifiable string that can be used to abort
        using the abort_listener method.

        :param callback: A function that takes a message and it's source nick
        :returns: A unique id for the listener, suitable for abort_listener(x)
        """
        pass

    @abc.abstractmethod
    def abort_listener(self, listener_id: str) -> None:
        """Abort a previously enabled listener.

        Implementations must not return on this method until they can guarantee
        the callback previously given to listen_for_messages will not be called again.

        :param listener_id: The unique identifier returned by listen_for_messages
        """
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
        responses: dict[str, Response] = {}

        def evaluate_response(id: str, nick: str, msg: str) -> None:
            print("Evaluating: {}, {}, {}".format(id, nick, msg))
            result = fuzz.ratio(
                utils.full_process(question.answer), utils.full_process(msg)
            )
            print(
                "Evaluated {} answer: {} as {}% correct".format(nick, msg, result)
            )
            if nick in responses and responses[nick].accuracy > result:
                return

            if result > 60:
                responses[nick] = Response(nick, msg, result)

        self.runner.message(
            [
                "Let's play Tastpardy! Only one question for now. "
                "You'll get 30 seconds to answer, then I'll check your work!",
                "Oh, and for now; just the answer. None of that questions as answers stuff.",
                "-------------------",
                "Air Date: {}. Difficulty: {}. Category: {}".format(
                    question.aired, question.difficulty, question.category.name
                ),
                "-------------------",
                str(question.question),
            ],
            target,
        )
        answers: list[str] = []
        listener_id = self.runner.listen_for_messages(evaluate_response)
        self.runner.wait(30)
        self.runner.abort_listener(listener_id)
        if len(responses) != 0:
            sorted(responses.values(), key=lambda x: x.accuracy, reverse=True)

        for r in responses.values():
            answers.append(str(r))

        if answers:
            self.runner.message(
                [
                    "The answer was: What is {}? Lets see who was closest!".format(
                        str(question.answer)
                    ),
                    "-------------------",
                ],
                target,
            )
            self.runner.message(answers, target)
        else:
            self.runner.message(
                [
                    "No one got it right! "
                    "The answer was: What is {}?".format(str(question.answer))
                ],
                target,
            )
