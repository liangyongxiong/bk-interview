# coding=utf-8


class ServiceException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return f'{self.__class__.__name__}({self.msg})'
