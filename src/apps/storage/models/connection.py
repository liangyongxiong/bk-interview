# coding=utf-8

from dataclasses import dataclass, asdict


@dataclass
class RedisConnection:

    host: str = ''
    port: int = 0
    password: str = ''

    def to_json(self):
        return asdict(self)


@dataclass
class MySQLConnection:

    host: str = ''
    port: int = 0
    username: str = ''
    password: str = ''

    def to_json(self):
        return asdict(self)
