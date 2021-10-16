# coding=utf-8

import enum
from typing import Optional

from pydantic import BaseModel, Field


class MySQLBinlogFormat(enum.Enum):
    STATEMENT = 'STATEMENT'
    ROW = 'ROW'
    MIXED = 'MIXED'


class MySQLCharset(enum.Enum):
    UTF8MB4 = 'utf8mb4'
    latin1 = 'latin1'


class MySQLConfig(BaseModel):
    charset: Optional[MySQLCharset] = Field(
                    MySQLCharset.UTF8MB4, example='utf8mb4',
                    description='The servers default character set.')
    binlog_format: Optional[MySQLBinlogFormat] = Field(
                    MySQLBinlogFormat.STATEMENT, example='STATEMENT',
                    description='Supported Binary Log Formats.')

    def dict(self):
        data = super().dict()
        data['charset'] = data['charset'].value
        data['binlog_format'] = data['binlog_format'].value
        return data
