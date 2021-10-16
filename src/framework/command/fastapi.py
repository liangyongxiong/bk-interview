# coding=utf-8

from framework.command.base import BaseCommand


class Command(BaseCommand):

    def register(self, subparser):
        parser = subparser.add_parser('fastapi', help='run fastapi application')
        parser.add_argument('--domain',
                            type=str, dest='domain', required=True,
                            help='specify domain for fastapi application')
        parser.add_argument('--host',
                            type=str, dest='host', default='0.0.0.0',
                            help='specify server host')
        parser.add_argument('--port',
                            type=int, dest='port', default=8080,
                            help='specify server port')
        parser.add_argument('--debug',
                            action='store_true', dest='debug', default=False,
                            help='enable the Uvicorn debugger')
        parser.add_argument('--reload',
                            action='store_true', dest='reload', default=False,
                            help='monitor Python files for changes')

    def invoke(self, args):
        import os
        import logging
        from uvicorn import Config, Server
        from framework.conf import settings
        from framework.fastapi.builder import FastAPIBuilder

        fastapi_app = FastAPIBuilder.get_domain_app(args.domain)
        if fastapi_app is None:
            return

        log_config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'default': {
                    '()': 'uvicorn.logging.DefaultFormatter',
                    'fmt': '%(asctime)s | %(levelname)s | (%(process)d:%(thread)d) - %(message)s',
                    'use_colors': False,
                },
                'access': {
                    '()': 'uvicorn.logging.AccessFormatter',
                    'fmt': '%(asctime)s | %(client_addr)s - "%(request_line)s" %(status_code)s',
                    'use_colors': False,
                },
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stderr',
                    'formatter': 'default',
                },
                'default': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'default',
                    'filename': os.path.join(settings.WORKSPACE, settings.LOG_FOLDER, 'uvicorn.error.log'),
                    'maxBytes': settings.LOGGING_ROTATE_MAX_BYTES,
                    'backupCount': settings.LOGGING_ROTATE_BACKUP_COUNT,
                    'encoding': 'utf8',
                },
                'access': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'formatter': 'access',
                    'filename': os.path.join(settings.WORKSPACE, settings.LOG_FOLDER, 'uvicorn.access.log'),
                    'maxBytes': settings.LOGGING_ROTATE_MAX_BYTES,
                    'backupCount': settings.LOGGING_ROTATE_BACKUP_COUNT,
                    'encoding': 'utf8',
                },
            },
            'loggers': {
                'uvicorn': {
                    'handlers': ['console', 'default'],
                    'level': logging.INFO,
                },
                'uvicorn.error': {
                    'handlers': ['console', 'default'],
                    'level': logging.INFO,
                    'propagate': False
                },
                'uvicorn.access': {
                    'handlers': ['access'],
                    'level': logging.INFO,
                    'propagate': False
                },
            },
        }

        headers = [
            ('Server', 'Linux'),
        ]

        config = Config(fastapi_app,
            host=args.host,
            port=args.port,
            debug=args.debug,
            reload=args.reload,
            workers=1,
            log_config=log_config,
            headers=headers)
        Server(config=config).run()
