# coding=utf-8

import enum
from typing import Dict


class ContainerStatus(enum.Enum):
    UNKNOWN = 'unknown'
    RUNNING = 'running'
    CREATED = 'created'
    EXITED = 'exited'


class ContainerInstance:

    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.ports = kwargs.get('ports')
        self.status = kwargs.get('status')

    def to_json(self):
        ports = {}
        for key, value in self.ports.items():
            if value is None:
                ports[key] = None
            else:
                ports[key] = []
                for item in value:
                    ports[key].append(f"{item['HostIp']}:{item['HostPort']}")

        return {
            'id': self.id,
            'name': self.name,
            'ports': ports,
            'status': self.status.value,
        }
