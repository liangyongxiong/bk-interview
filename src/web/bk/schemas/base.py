# coding=utf-8

from typing import Optional, Union, Any

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    err: int = 0
    msg: Optional[str] = ''
    data: Optional[Union[dict, list, None]] = Field(None, example='null')
