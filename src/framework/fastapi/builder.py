# coding=utf-8

import sys
import os
import logging
from importlib import import_module
from logging.handlers import RotatingFileHandler

import loguru
from attrdict import AttrDict
from starlette.requests import Request
from starlette.exceptions import HTTPException
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi import FastAPI, APIRouter, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from framework.conf import settings
from framework.exception import ServiceException
from framework.jinja2 import FILTERS, TESTS
from framework.fastapi.middlewares import RequestMiddleware, RedisSessionMiddleware


class FastAPIBuilder:

    @classmethod
    def get_domain_app(cls, domain):
        if not domain:
            print('missing domain for flask application')
            return None

        module_path = f'web.{domain}.fastapi'
        try:
            module = import_module(module_path)
        except ModuleNotFoundError:
            builder_cls = cls
        else:
            builder_cls = getattr(module, 'Builder', None)
            if builder_cls is None or not issubclass(builder_cls, cls):
                print(f'invalid flask build path {module_path}.Builder')
                return None

        builder = builder_cls(domain)
        builder.make()
        return builder.app

    def __init__(self, domain):
        self.domain = domain
        self.domain_dir = os.path.join(settings.ROOT, 'web', domain)
        self.config = AttrDict()
        self.app = None
        self.logger = None
        self.globals = {}

    def make(self):
        self.init_config()

        fastapi_kwargs = {'debug': self.config.DEBUG}
        if self.config.DEBUG:
            fastapi_kwargs.update(**dict(
                openapi_url=self.config.OPENAPI_URL,
                docs_url=self.config.DOCS_URL,
                redoc_url=self.config.REDOC_URL,
            ))
        else:
            fastapi_kwargs.update(**dict(
                openapi_url=None,
                docs_url=None,
                redoc_url=None,
            ))

        self.app = FastAPI(title=settings.NAME, **fastapi_kwargs)

        if hasattr(self.config, 'STATIC_FOLDER'):
            path = os.path.join(settings.ROOT, self.config.STATIC_FOLDER)
            if os.path.exists(path):
                self.app.mount('/static', StaticFiles(directory=path), name='static')

        self.setup_logging()
        self.setup_jinja2()
        self.setup_exception_handlers()
        self.setup_event_handlers()
        self.setup_middlewares()
        self.setup_routes()

    def init_config(self):
        try:
            domain_config = import_module(f'web.{self.domain}.conf.config')
        except ModuleNotFoundError as e:
            raise e

        default_config = import_module('framework.fastapi.config')
        for setting in dir(default_config):
            if setting.isupper():
                setting_value = getattr(default_config, setting)
                setattr(self.config, setting, setting_value)

        prefix = 'FASTAPI_'
        for setting in dir(domain_config):
            if setting.isupper() and setting.startswith(prefix):
                setting_value = getattr(domain_config, setting)
                setattr(self.config, setting[len(prefix):], setting_value)

        if hasattr(domain_config, 'WEB'):
            setattr(self.config, 'WEB', AttrDict(domain_config.WEB))

    def setup_logging(self):
        sink = RotatingFileHandler(
            filename=os.path.join(settings.WORKSPACE, settings.LOG_FOLDER, f'fastapi.{self.domain}.log'),
            maxBytes=settings.LOGGING_ROTATE_MAX_BYTES,
            backupCount=settings.LOGGING_ROTATE_BACKUP_COUNT,
            encoding='utf8')
        logging_level = logging.DEBUG if self.config.DEBUG else settings.LOGGING_LEVEL
        logging_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | " \
                        "<level>{level}</level> | " \
                        "<cyan>({process},{thread})</cyan> - " \
                        "<level>[{extra[mdc]}] {message}</level>"

        logger = loguru.logger
        logger.remove()
        logger.configure(extra={'mdc': '------'})
        logger.add(
            sink=sys.stderr,
            level=logging_level,
            format=logging_format,
            filter=lambda record: record['extra'].get('name') == 'fastapi')
        logger.add(
            sink=sink,
            level=logging_level,
            format=logging_format,
            filter=lambda record: record['extra'].get('name') == 'fastapi')
        self.logger = logger.bind(name='fastapi')
        self.app.logger = self.logger

    def setup_jinja2(self):
        path = os.path.join(self.domain_dir, self.config.TEMPLATE_FOLDER)
        if not os.path.exists(path):
            return

        self.app.jinja_templates = Jinja2Templates(directory=path)
        env = self.app.jinja_templates.env
        env.filters.update(FILTERS)
        env.tests.update(TESTS)
        env.globals.update({'WEB': self.config.WEB})

    def setup_middlewares(self):
        if self.config.ENABLE_GZIP:
            self.app.add_middleware(GZipMiddleware, minimum_size=1000)

        if self.config.ENABLE_CORS:
            self.app.add_middleware(CORSMiddleware,
                                    max_age=self.config.ACCESS_CONTROL_MAX_AGE,
                                    allow_origins=self.config.CORS_WHITELIST_DOMAINS,
                                    allow_credentials=True,
                                    allow_methods=['*'],
                                    allow_headers=['*'])

        if self.config.ENABLE_SESSION:
            if getattr(settings, 'REDIS', None) and self.config.SESSION_REDIS_ALIAS in settings.REDIS:
                self.app.add_middleware(RedisSessionMiddleware, config=self.config, logger=self.logger)
            else:
                self.app.add_middleware(SessionMiddleware, secret_key=self.config.SESSION_SECRET_KEY)

        self.app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=['*'])
        self.app.add_middleware(RequestMiddleware, config=self.config)

    def setup_exception_handlers(self):
        self.app.add_exception_handler(Exception, self.generic_exception_handler)
        self.app.add_exception_handler(ServiceException, self.generic_exception_handler)
        self.app.add_exception_handler(RequestValidationError, self.request_validation_error_handler)
        self.app.add_exception_handler(HTTPException, self.http_exception_handler)

    def generic_exception_handler(self, request: Request, exc: Exception):
        logger = request.state.logger
        endpoint = request.scope.get('endpoint')
        if endpoint:
            logger.error(f'[endpoint] {endpoint.__module__}.{endpoint.__name__}')

        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=dict(err=1, msg=str(exc))
        )
        response.headers['X-Request-Id'] = request.state.id
        return response

    def request_validation_error_handler(self, request: Request, exc: RequestValidationError):
        logger = request.state.logger
        endpoint = request.scope.get('endpoint')
        if endpoint:
            logger.error(f'[endpoint] {endpoint.__module__}.{endpoint.__name__}')

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=dict(err=1, msg='Request Validation Error.', data=jsonable_encoder(exc.errors()))
        )

    def http_exception_handler(self, request: Request, exc: HTTPException):
        logger = request.state.logger
        endpoint = request.scope.get('endpoint')
        if endpoint:
            logger.error(f'[endpoint] {endpoint.__module__}.{endpoint.__name__}')

        return HTMLResponse(status_code=exc.status_code, content=f'{exc.status_code} - {exc.detail}')

    def setup_event_handlers(self):
        self.app.add_event_handler('startup', self.on_startup)
        self.app.add_event_handler('shutdown', self.on_shutdown)

    def on_startup(self):
        pass

    def on_shutdown(self):
        pass

    def setup_routes(self):
        base_path = os.path.join(self.domain_dir, 'routers')
        for filename in os.listdir(base_path):
            full_pathname = os.path.join(base_path, filename)
            if not filename.endswith('.py') or not os.path.isfile(full_pathname):
                continue
            module_path = full_pathname[len(settings.ROOT) + 1:-len('.py')].replace(os.sep, '.')
            module = import_module(module_path)
            router = getattr(module, 'router', None)
            if router and isinstance(router, APIRouter):
                self.app.include_router(router)
