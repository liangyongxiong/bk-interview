# coding=utf-8

import random
import threading
import docker

from ..models.container import ContainerInstance, ContainerStatus
from framework.conf import settings
from framework.exception import ServiceException
from framework.utils import check_connection


class BaseManager:

    _mutex = threading.Lock()
    _instance = None

    image_tag = ''

    def __new__(cls, logger, *args, **kwargs):
        with cls._mutex:
            if cls._instance is None:
                cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance

    @classmethod
    def init(cls, logger=None):
        cls._instance = cls(logger)

    @classmethod
    def instance(cls):
        return cls._instance

    def __init__(self, logger):
        self.logger = logger
        self.docker_client = None
        try:
            self.docker_client = docker.DockerClient(base_url=settings.DOCKER_BASE_URL)
        except docker.errors.DockerException:
            pass

    def list(self):
        containers = []
        for container in self.docker_client.containers.list(all=True):
            if self.image_tag not in container.image.tags:
                continue
            containers.append(ContainerInstance(
                id=container.short_id,
                name=container.name,
                ports=container.ports,
                status=ContainerStatus(container.status)))

        return containers

    def get(self, container_id: str = ''):
        try:
            container = self.docker_client.containers.get(container_id)
        except docker.errors.NotFound:
            raise ServiceException('容器实例不存在')

        if self.image_tag not in container.image.tags:
            raise ServiceException('容器实例与存储资源类型不符')

        return container

    def create(self, config: dict = dict()):
        raise NotImplementedError

    def remove(self, container_id: str = ''):
        container = self.get(container_id)
        container.stop()
        container.remove()
        return True

    def generate_random_password(self):
        upper_alphabet_chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        lower_alphabet_chars = 'abcdefghijklmnopqrstuvwxyz'
        numeric_chars = '0123456789'
        special_chars = '!@#$%^&*()<>?[],.'
        password_chars = random.sample(upper_alphabet_chars, 3)
        password_chars += random.sample(lower_alphabet_chars, 3)
        password_chars += random.sample(numeric_chars, 3)
        password_chars += random.sample(special_chars, 3)
        random.shuffle(password_chars)
        return ''.join(password_chars)

    def generate_random_volume(self):
        volume_name_chars = random.sample('0123456789abcdef', 6)
        random.shuffle(volume_name_chars)
        return ''.join(volume_name_chars)

    def pick_random_port(self):
        max_tries = 10
        while max_tries > 0:
            max_tries -= 1
            port = random.choice(range(10000, 60000))
            if not check_connection(settings.DOCKER_HOST_IP, port):
                return port
        return 0
