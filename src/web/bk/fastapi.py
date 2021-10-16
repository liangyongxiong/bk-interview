# coding=utf-8

from importlib import import_module

from framework.conf import settings
from framework.fastapi.builder import FastAPIBuilder
from apps.storage.managers.redis import RedisManager
from apps.storage.managers.mysql import MySQLManager


class Builder(FastAPIBuilder):

    def on_startup(self):
        self.logger.info('Services init.')
        RedisManager.init(self.logger)
        MySQLManager.init(self.logger)
        self.logger.info('Services ready.')
