from dataclasses import dataclass
from dataclasses_json import dataclass_json

import json

@dataclass_json
@dataclass
class IRCConfig:
    server: str
    port: int
    ssl: bool
    nick: str
    pw: str
    channel: str
    admins: list[str]

@dataclass_json
@dataclass
class Config:
    irc: list[IRCConfig]
    dbpath: str