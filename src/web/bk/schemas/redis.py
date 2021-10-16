# coding=utf-8

import enum
from typing import Optional

from pydantic import BaseModel, Field


class RedisAppendFSync(enum.Enum):
    ALWAYS = 'always'
    EVERYSEC = 'everysec'
    NO = 'no'


class RedisConfig(BaseModel):
    maxmemory: Optional[int] = Field(
                    0, ge=0, example=1000,
                    description="Don't use more memory than the specified amount of bytes.")
    maxclients: Optional[int] = Field(
                    10000, gt=0, example=100,
                    description="Set the max number of connected clients at the same time.")
    appendfsync: Optional[RedisAppendFSync] = Field(
                    RedisAppendFSync.EVERYSEC, example='everysec',
                    description='The fsync() call tells the Operating System to actually write data on disk.')

    def dict(self):
        data = super().dict()
        data['appendfsync'] = data['appendfsync'].value
        return data
