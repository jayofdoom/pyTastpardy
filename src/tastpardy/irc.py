import copy
from dataclasses import dataclass
import ssl
import time
from typing import Any, Callable
import uuid

import eventlet
from irc.bot import ExponentialBackoff, SingleServerIRCBot
from irc.connection import Factory
import irc.strings

from tastpardy.command import CommandRegistry
from tastpardy.config import IRCConfig
from tastpardy.game import ChannelStats, Game, GameRunner


irc_registry = CommandRegistry()


class TastyIRCBot(SingleServerIRCBot, GameRunner):
    def __init__(self, dbpath: str, conf: IRCConfig):
        self.conf = conf
        self.channel = self.conf.channel
        self.game = Game(self, dbpath=dbpath)
        self.message_listeners: dict[str, Callable[[str, str, str], None]] = {}

        self.pool = eventlet.GreenPool()
        self.gamePool = eventlet.GreenPool()

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
        eventlet.sleep(int(seconds))

    def channel_stats(self) -> ChannelStats:
        chname, chobj = self.channels[0]
        return ChannelStats(
            members=chobj.users(),
            topic=chobj.topic,
            name=chname,
        )

    def listen_for_messages(self, callback: Callable[[str, str, str], None]) -> str:
        listener_id = str(uuid.uuid4())
        print("Registering listener: {}".format(listener_id))
        self.message_listeners[listener_id] = callback
        return listener_id

    def abort_listener(self, listener_id: str) -> None:
        del self.message_listeners[listener_id]

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
        if e.source.nick.lower() == self.connection.get_nickname().lower():
            return None

        listeners = self.message_listeners.copy()
        def run_listener(listener: tuple[str, Callable[[str, str, str], None]]) -> None:
            listener_id = copy.deepcopy(listener[0])
            runner = copy.deepcopy(listener[1])
            if runner is not None:
                runner(listener_id, e.source.nick, e.arguments[0])

        def handle_pubmsg():
            if e.arguments[0][0] == "?":
                self.handle_command(
                    e.source.nick, e.arguments[0][1:].strip(), self.channel
                )
            else:
                target_nick = e.arguments[0].split(":", 1)[0].strip()
                if target_nick and irc.strings.lower(target_nick) == irc.strings.lower(
                    self.connection.get_nickname()
                ):
                    self.handle_command(
                        e.source.nick,
                        e.arguments[0].split(":", 1)[1].strip(),
                        self.channel,
                    )

        if listeners:
            self.pool.imap(run_listener, listeners.items())

        self.pool.spawn_n(handle_pubmsg)

        return None

    def handle_command(self, nick: str, cmd_name: str, target: str):
        # Always prioritize IRC commands over game commands
        if cmd_name in irc_registry.commands:
            cmd = irc_registry.commands[cmd_name]
            if cmd.admin and self.conf.admins:
                if nick not in self.conf.admins:
                    self.not_tasty(nick)
                    return

            if cmd and cmd.exec:
                self.pool.spawn_n(cmd.exec, self, nick, target)

        return None

    def not_tasty(self, nick: str):
        self.connection.notice(nick, "Not tasty.")

    @irc_registry.register("question")
    def question(self, nick: str, target: str):
        self.pool.spawn_n(self.game.single_question, target)

    @irc_registry.register("botsnacks")
    def botsnacks(self, nick: str, target: str):
        self.connection.privmsg(target, "It's Tasty Tasty, very very Tasty!")

    @irc_registry.register("stats", admin=True)
    def stats(self, nick: str, target: str):
        for chname, chobj in self.channels.items():
            self.connection.notice(nick, "--- Channel statistics ---")
            self.connection.notice(nick, "Channel: " + chname)
            self.connection.notice(nick, "Users: " + ", ".join(sorted(chobj.users())))
            self.connection.notice(nick, "Opers: " + ", ".join(sorted(chobj.opers())))
            self.connection.notice(nick, "Voiced: " + ", ".join(sorted(chobj.voiced())))

    @irc_registry.register("disconnect", admin=True)
    def disconnect(self, nick: str, target: str):
        self.connection.disconnect(
            "My manager, {} said I could go home early.".format(nick)
        )
        exit(0)
