from dataclasses import dataclass
import ssl
import time
from typing import Any, Callable

from irc.bot import ExponentialBackoff, SingleServerIRCBot
from irc.connection import Factory
import irc.strings

from tastpardy.config import IRCConfig
from tastpardy.game import Game, GameRunner


@dataclass
class BotCommand(object):
    admin: bool
    func: Callable[[Any, str, str], Any]


commands: dict[str, BotCommand] = {}


def command(name: str, admin: bool = False):
    def decorator(func: Callable[[Any, str, str], None]):
        commands[name] = BotCommand(admin=admin, func=func)
        return func

    return decorator


class TastyIRCBot(SingleServerIRCBot, GameRunner):
    def __init__(self, dbpath: str, conf: IRCConfig):
        self.conf = conf
        self.channel = self.conf.channel
        self.game = Game(self, dbpath=dbpath)

        connect_params = {}
        if conf.ssl:
            connect_params["connect_factory"] = Factory(wrapper=ssl.wrap_socket)  # type: ignore
        super(TastyIRCBot, self).__init__(
            [(conf.server, conf.port)],
            conf.nick,
            None,
            recon=ExponentialBackoff(),
            **connect_params,
        )

    def message(self, message: list[str], target):
        if target == self.channel:
            msg_func: Callable = self.connection.privmsg
        else:
            msg_func = self.connection.notice
        for m in message:
            msg_func(target, m)

    def wait(self, seconds: int | float):
        time.sleep(seconds)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        if self.conf.pw:
            c.privmsg("NickServ", "IDENTIFY {}".format(self.conf.pw))
        time.sleep(5)
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.handle_command(e.source.nick, e.arguments[0], e.source.nick)

    def on_pubmsg(self, c, e):
        if e.arguments[0][0] == "?":
            self.handle_command(e.source.nick, e.arguments[0][1:].strip(), self.channel)
        else:
            target_nick = e.arguments[0].split(":", 1)[0].strip()
            if target_nick and irc.strings.lower(target_nick) == irc.strings.lower(
                self.connection.get_nickname()
            ):
                self.handle_command(
                    e.source.nick, e.arguments[0].split(":", 1)[1].strip(), self.channel
                )

    def handle_command(self, nick: str, cmd: str, target: str):
        if cmd in commands:
            if commands[cmd].admin and self.conf.admins:
                if nick not in self.conf.admins:
                    self.not_tasty(nick)
                    return

            commands[cmd].func(self, nick, target)
        else:
            self.not_tasty(nick)

    def not_tasty(self, nick: str):
        self.connection.notice(nick, "Not tasty.")

    @command("question")
    def single_question(self, nick: str, target: str):
        self.game.single_question(target)

    @command("stats", admin=True)
    def stats(self, nick: str, target: str):
        for chname, chobj in self.channels.items():
            self.connection.notice(nick, "--- Channel statistics ---")
            self.connection.notice(nick, "Channel: " + chname)
            self.connection.notice(nick, "Users: " + ", ".join(sorted(chobj.users())))
            self.connection.notice(nick, "Opers: " + ", ".join(sorted(chobj.opers())))
            self.connection.notice(nick, "Voiced: " + ", ".join(sorted(chobj.voiced())))

    @command("botsnacks")
    def botsnacks(self, nick: str, target: str):
        self.connection.privmsg(target, "It's Tasty Tasty, very very Tasty!")

    @command("disconnect", admin=True)
    def disconnect(self, nick: str, target: str):
        self.connection.disconnect(
            "My manager, {} said I could go home early.".format(nick)
        )
        exit(0)
