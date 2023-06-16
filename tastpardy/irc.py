from dataclasses import dataclass
import ssl
import time
from typing import Callable

import irc.bot
import irc.connection
import irc.strings

from tastpardy.config import IRCConfig
from tastpardy.game import Game, GameRunner


@dataclass
class BotCommand(object):
    admin: bool
    func: Callable


commands : dict[str, BotCommand] = {}


def command(name: str, admin: bool=False):
    def decorator(func: Callable):
        commands[name] = BotCommand(admin=admin, func=func)
        return func
    return decorator


class TastyIRCBot(irc.bot.SingleServerIRCBot, GameRunner):
    def __init__(self, dbpath : str, conf : IRCConfig):
        self.conf = conf
        self.channel = self.conf.channel
        # I'll have to figure out some kind of interface to send messages to/from the game
        # so that it'll be at least theorertically capable of running on more than just IRC
        self.game = Game(self, dbpath=dbpath)

        connect_params = {}
        if conf.ssl:
            connect_params["connect_factory"] = irc.connection.Factory(wrapper=ssl.wrap_socket)  # type: ignore
        irc.bot.SingleServerIRCBot.__init__(self, [(conf.server, conf.port)], conf.nick, None, recon=irc.bot.ExponentialBackoff(), **connect_params)

        # Register commands from the base class
        command("disconnect", admin=True)(self.disconnect)
        command("die", admin=True)(self.die)
    
    def public_message(self, message: list[str]):
        for m in message:
            self.connection.privmsg(self.channel, m)

    def private_message(self, nick: str, message: list[str]):
        for m in message:
            self.connection.privmsg(nick, m)

    def wait(self, seconds: int|float):
        time.sleep(seconds)

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        if self.conf.pw:
            c.privmsg("NickServ", "IDENTIFY {}".format(self.conf.pw))
        time.sleep(5)
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.connection.privmsg(e.source.nick, "Don't eat in secret, be proud and tasty. Only message me in channel.")

    def on_pubmsg(self, c, e):
        if e.arguments[0][0] == "?":
            self.handle_command(e.source.nick, e.arguments[0][1:].strip())
        else:
            target_nick = e.arguments[0].split(":", 1)[0].strip()
            if target_nick and irc.strings.lower(target_nick) == irc.strings.lower(self.connection.get_nickname()):
                self.handle_command(e.source.nick, e.arguments[0].split(":", 1)[1].strip())

    def handle_command(self, nick, cmd):
        if cmd in commands:
            if commands[cmd].admin and self.conf.admins:
                if nick not in self.conf.admins:
                   self.not_tasty(nick)
                   return

            commands[cmd].func(self, nick)
        else:
            self.not_tasty(nick)
    
    def not_tasty(self, nick):
        self.connection.notice(nick, "Not tasty.")

    @command("question")
    def single_question(self, nick):
        self.game.single_question()

    @command("stats", admin=True)
    def stats(self, nick):
        for chname, chobj in self.channels.items():
            self.connection.notice(nick, "--- Channel statistics ---")
            self.connection.notice(nick, "Channel: " + chname)
            self.connection.notice(nick, "Users: " + ", ".join(sorted(chobj.users())))
            self.connection.notice(nick, "Opers: " + ", ".join(sorted(chobj.opers())))
            self.connection.notice(nick, "Voiced: " + ", ".join(sorted(chobj.voiced())))

    @command("botsnacks")
    def botsnacks(self, nick):
        self.connection.privmsg(self.channel, "It's Tasty Tasty, very very Tasty!")
