# coding=utf-8

import re
import json
from importlib import import_module

import loguru
import shortuuid
from bson import ObjectId
from attrdict import AttrDict
from itsdangerous import TimestampSigner
from starlette.requests import HTTPConnection
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import UploadFile
from starlette.datastructures import MutableHeaders
from starlette.types import Message
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import status


class RequestMiddleware(BaseHTTPMiddleware):

    def __init__(self, app, config: AttrDict):
        super().__init__(app, dispatch=None)
        self.config = config
        self.uuid = shortuuid.ShortUUID(alphabet='0123456789ABCDEF')

    async def dispatch(self, request, call_next):
        await self.hook_before_request(request)
        response = await call_next(request)
        await self.hook_after_request(request, response)
        return response

    async def hook_before_request(self, request: Request):
        if request.url.path.startswith('/static'):
            return

        request.state.is_mobile = self.is_mobile(request)
        request.state.is_weixin = self.is_weixin(request)
        request.state.id = self.uuid.random(length=6)
        patcher = lambda record: record['extra'].update(mdc=request.state.id)
        logger = loguru.logger.bind(name='fastapi').patch(patcher)
        request.state.logger = logger

        logger.info(f'[uri] {request.method} {request.url.path}')

        if request.url.query:
            logger.info(f'[query] {request.url.query}')

        logger.info(f'[headers] {dict(request.headers)}')

    async def hook_after_request(self, request: Request, response: Response):
        if request.url.path.startswith('/static'):
            if request.url.path.endswith('.ejs'):
                response.headers['Content-Type'] = 'text/html; charset=utf-8'
            return response

        logger = request.state.logger
        endpoint = request.scope.get('endpoint')
        if endpoint:
            logger.info(f'[endpoint] {endpoint.__module__}.{endpoint.__name__}')

        response.headers['X-Request-Id'] = request.state.id

        if response.status_code >= status.HTTP_400_BAD_REQUEST:
            logger.error(f'[http] {response.status_code}')
        elif status.HTTP_300_MULTIPLE_CHOICES <= response.status_code < status.HTTP_400_BAD_REQUEST:
            logger.warning(f'[http] {response.status_code}')
        else:
            logger.info(f'[http] {response.status_code}')

    def is_mobile(self, request: Request):
        agent = request.headers.get('User-Agent')
        if not agent:
            return False
        features = ['android', 'iphone', 'ipad', 'ipod', 'windows phone', 'symbian', 'blackberry']
        matcher = re.search('|'.join(features), agent, re.I)
        return matcher is not None

    def is_weixin(self, request: Request):
        agent = request.headers.get('User-Agent')
        if not agent:
            return False
        matcher = re.search('micromessenger', agent, re.I)
        return matcher is not None


class RedisSessionMiddleware:

    def __init__(self, app, config: AttrDict, logger):
        self.app = app
        self.config = config
        self.logger = logger
        self.signer = TimestampSigner(config.SESSION_SECRET_KEY)

        redis_mgr = import_module('framework.redis').getattr('RedisManager').instance()
        redis_mgr.init_redis(config.SESSION_REDIS_ALIAS)
        self.redis = redis_mgr.get(config.SESSION_REDIS_ALIAS)

    async def __call__(self, scope, receive, send):
        if scope['type'] not in ('http', 'websocket'):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        connection = HTTPConnection(scope)
        is_empty_session = True

        scope['session'] = {}
        if self.config.SESSION_COOKIE_NAME in connection.cookies:
            session_id = connection.cookies[self.config.SESSION_COOKIE_NAME]
            redis_key = f'{self.config.SESSION_KEY_PREFIX}{session_id}'
            scope['session'] = json.loads(self.redis.get(redis_key))
            scope['session_id'] = session_id
            is_empty_session = False

        async def send_wrapper(message: Message, **kwargs) -> None:
            if message['type'] == 'http.response.start':
                session_id = scope.pop('session_id', str(ObjectId()))
                redis_key = f'{self.config.SESSION_KEY_PREFIX}{session_id}'

                if scope['session']:
                    self.redis.set(redis_key, json.dumps(scope['session']))
                    self.redis.expire(redis_key, self.config.SESSION_COOKIE_MAXAGE)
                    headers = MutableHeaders(scope=message)
                    header_value = self._construct_cookie(session_id=session_id, clear=False)
                    headers.append('Set-Cookie', header_value)

                elif not is_empty_session:
                    self.redis.delete(redis_key)
                    headers = MutableHeaders(scope=message)
                    header_value = self._construct_cookie(clear=True)
                    headers.append('Set-Cookie', header_value)

            await send(message)

        await self.app(scope, receive, send_wrapper)

    def _construct_cookie(self, session_id=None, clear: bool = False):
        cookie_expire = 'Thu, 01 Jan 1970 00:00:00 GMT'
        cookie_max_age = 0 if clear else self.config.SESSION_COOKIE_MAXAGE

        cookie = f'{self.config.SESSION_COOKIE_NAME}={session_id};'
        cookie += ' Path=/;'
        cookie += f' Max-Age={cookie_max_age};'
        if clear:
            cookie += f' Expires={cookie_expire};'

        if self.config.SESSION_COOKIE_HTTPONLY:
            cookie += ' httponly;'
        if self.config.SESSION_COOKIE_SECURE:
            cookie += ' secure;'
        if self.config.SESSION_COOKIE_SAMESITE:
            cookie += f' samesite={self.config.SESSION_COOKIE_SAMESITE};'
        if self.config.SESSION_COOKIE_DOMAIN:
            cookie += f' Domain={self.config.SESSION_COOKIE_DOMAIN};'

        return cookie
