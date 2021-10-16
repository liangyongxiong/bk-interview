# -*- coding: utf-8 -*-

import os
import sys
import time
import traceback
from importlib import import_module

from framework.conf import defaults


class Settings:

    _explicit_settings = set()

    def __init__(self):
        # update this dict from default settings (but only for ALL_CAPS settings)
        for setting in dir(defaults):
            if setting.isupper():
                setattr(self, setting, getattr(defaults, setting))

        try:
            module = import_module('conf.config')
        except ModuleNotFoundError:
            traceback.print_exc()
            sys.exit(0)

        for setting in dir(module):
            if setting.isupper():
                setting_value = getattr(module, setting)
                setattr(self, setting, setting_value)
                self._explicit_settings.add(setting)

        if hasattr(time, 'tzset') and self.TIME_ZONE:
            os.environ['TZ'] = self.TIME_ZONE
            time.tzset()

    def is_overridden(self, setting):
        return setting in self._explicit_settings

    def convert_prefix_config(self, prefix):
        config = {}
        for setting in dir(self):
            if setting.isupper() and setting.startswith(prefix):
                config[setting[len(prefix):]] = getattr(self, setting)

        return config

    def dump(self):
        config = {}
        for setting in dir(self):
            if setting.isupper():
                config[setting] = getattr(self, setting)

        return config


settings = Settings()
