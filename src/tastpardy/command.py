from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Command:
    name: str
    admin: bool
    exec: Callable[[Any, str, str], Any]


class CommandRegistry(object):
    def __init__(self):
        self.commands: dict[str, Command] = {}

    def __contains__(self, name: str) -> bool:
        return name in self.commands

    def register(self, name: str, admin: bool = False):
        def decorator(func: Callable[[Any, str, str], None]):
            self.commands[name] = Command(name=name, admin=admin, exec=func)
            return func

        return decorator

    def __get__(self, name: str) -> Command:
        return self.commands[name]
