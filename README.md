pyTastpardy
===========
A python game bot. Mainly a personal playground for seeing how helpful AI code
generation can be while working with libraries I'm fairly familiar with. What
does this mean? Don't expect it to be stable/well-supported. If anyone ever
cares to use this, open an issue or something and maybe I'll get serious :).

Usage
=====
doesn't exist yet, but probably would look like

`python -m tastpardy  --config ./path/to/config.json --dbpath ./path/to/data.db`

Vision
======
Eventually I want to have a bot that does some of the following things:

Commands
--------
* question - return a single question, and the answer shortly thereafter.
* play - play a trivia game where your points are lost if you answer wrong
* score [player] - send the user a notice with information about [player's]
  score

A minimal set of administrative commands will also be runnable by users with
higher privledges. IDK what all these are yet.

Chat servers supported
----------------------
I'm starting with IRC, because it's easy, but I'd eventually like to hook the
commands into a discord or slack app.

Question sources
================
Right now, I'm loading in questions from a local backup of a j-archive dump. I
would love info on free-as-in-speech trivia question sources to use in tests
and examples.

Tests
=====
lol