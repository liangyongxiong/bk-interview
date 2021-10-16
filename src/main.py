# coding=utf-8

import sys
import os
from importlib import import_module


if __name__ == '__main__':
    if sys.version_info < (3, 7):
        print('python 3.7+ is required')
        sys.exit(0)

    # monkey = import_module('gevent.monkey')
    # monkey.patch_all()

    sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))

    try:
        import_module('framework.command.base').Manager().run()
    except KeyboardInterrupt:
        sys.exit(0)
