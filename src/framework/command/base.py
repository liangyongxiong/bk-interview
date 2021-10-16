# coding=utf-8

import sys
import os
import argparse
from importlib import import_module

import loguru

from framework.conf import settings


class BaseCommand:

    def register(self, subparser):
        raise NotImplementedError

    def invoke(self, args):
        raise NotImplementedError


class Manager:

    def __init__(self):
        # set umask to 0o077
        #import stat
        #os.umask(stat.S_IRXWG | stat.S_IRWXO)

        os.makedirs(os.path.join(settings.WORKSPACE, settings.LOG_FOLDER), exist_ok=True)

        loguru.logger._core.handlers.pop(0)
        loguru.logger.add(sys.stderr, format=settings.LOGURU_DEFAULT_FORMAT)

        self.parser = argparse.ArgumentParser(description=f'help for {settings.NAME} entrypoint')
        self.commands = {}
        self.init_parser()

    def init_parser(self):
        self.parser.add_argument('--version',
                                 action='version',
                                 version=settings.VERSION)

        subparser = self.parser.add_subparsers(dest='cmd')

        cmd_module_names = ['fastapi', 'clean']
        for cmd in cmd_module_names:
            cmd_module = import_module(f'framework.command.{cmd}')
            cmd_class = getattr(cmd_module, 'Command', None)
            cmd_instance = cmd_class()
            cmd_instance.register(subparser)
            self.commands[cmd] = cmd_instance

    def run(self):
        argv = sys.argv[1:] if len(sys.argv[1:]) else ['-h']
        args = self.parser.parse_args(argv)
        cmd = args.__dict__.pop('cmd')
        self.commands[cmd].invoke(args)
