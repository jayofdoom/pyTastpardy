import ssl
import time
import uuid

from sqlalchemy import func
import irc.bot  # type: ignore
import irc.connection  # type: ignore
import irc.strings  # type: ignore

from tastpardy.db import DBClient
from tastpardy.models import Question


class Game(object):
    def __init__(self):
        self.id = uuid.uuid4()
        self.session = DBClient().get_session()
    
    def single_question(self):
        question = self.session.query(Question).order_by(func.random()).limit(1).one()
        return question


class TastyBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channel, nickname, server, port=6667, use_ssl=False, password=None, admins=None):
        self.password = password
        self.admins = admins

        # I'll have to figure out some kind of interface to send messages to/from the game
        # so that it'll be at least theorertically capable of running on more than just IRC
        self.game = Game()

        connect_params = {}
        if use_ssl:
            connect_params["connect_factory"] = irc.connection.Factory(wrapper=ssl.wrap_socket)  # type: ignore
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname, None, recon=irc.bot.ExponentialBackoff(), **connect_params)
        self.channel = channel

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        if self.password:
            c.privmsg("NickServ", "IDENTIFY {}".format(self.password))
        time.sleep(5)
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        a = e.arguments[0].split(":", 1)
        if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(
            self.connection.get_nickname()
        ):
            self.do_command(e, a[1].strip())
        return
    
    def single_question(self, c):
        c.privmsg(self.channel,
                  "Let's play Tastpardy! Only one question though, because I'm lazy. "
                  "You'll get 30 seconds to think, then I'll give you the answer!")
        question = self.game.single_question()
        c.privmsg(self.channel, "-------------------")
        c.privmsg(self.channel,
                  "Air Date: {}. "
                  "Difficulty: {}. "
                  "Category: {}"
                  .format(question.aired,
                          question.difficulty,
                          question.category.name))
        c.privmsg(self.channel, "-------------------")
        c.privmsg(self.channel, question.question)
        time.sleep(30)
        c.privmsg(self.channel, "The answer was: What is {}? I hope you got it right!".format(question.answer))

    def admin_command(self, nick, runner, *args):
        # Check if nick is an admin. If we have no admins, YOLO.
        # Warning: this means there is basically zero security if you use
        # an IRC network with weak services.
        if not self.admins or nick in self.admins:
            runner(*args)
        else:
            raise PermissionError("You are not an admin.")

    def _stats(self, c, nick):
        for chname, chobj in self.channels.items():
            c.notice(nick, "--- Channel statistics ---")
            c.notice(nick, "Channel: " + chname)
            users = sorted(chobj.users())
            c.notice(nick, "Users: " + ", ".join(users))
            opers = sorted(chobj.opers())
            c.notice(nick, "Opers: " + ", ".join(opers))
            voiced = sorted(chobj.voiced())
            c.notice(nick, "Voiced: " + ", ".join(voiced))

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection

        try:
            if cmd == "botsnacks":
                c.privmsg(self.channel, "It's Tasty Tasty, very very Tasty!")
            elif cmd == "question":
                self.single_question(c)
            elif cmd == "disconnect":
                self.admin_command(nick, self.disconnect)
            elif cmd == "die":
                self.admin_command(nick, self.die)
            elif cmd == "stats":
                self.admin_command(nick, self._stats, c, nick)
            else:
                c.notice(nick, "Not tasty.")
        except PermissionError:
            c.notice(nick, "Not tasty.")