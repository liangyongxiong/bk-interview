# coding=utf-8

import os
import stat
import time
import jinja2
import docker

from framework.conf import settings
from framework.exception import ServiceException
from .base import BaseManager
from ..models.container import ContainerInstance, ContainerStatus
from ..models.connection import RedisConnection


class RedisManager(BaseManager):

    image_tag = 'redis:latest'

    def info(self, container_id: str):
        container = self.get(container_id)
        config_path = None
        for item in container.attrs['Mounts']:
            if item['Destination'] == '/opt':
                config_path = f"{item['Source']}/redis.conf"
                break
        if config_path is None:
            raise ServiceException('容器实例中未发现配置文件')

        with open(config_path, 'r') as fp:
            content = fp.read()

        config_info = {}
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            segments = line.split()
            key = segments[0]
            value = ' '.join(segments[1:])
            config_info[key] = value.strip('"').strip("'")

        return config_info

    def generate_config_file(self, config: dict, volume_path: str):
        template_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, 'templates'))
        jinja2_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir), autoescape=True)
        template = jinja2_env.get_template('redis.conf')
        with open(f'{volume_path}/redis.conf', 'w') as fp:
            fp.write(template.render(**config))

    def create(self, config: dict = dict()):
        password = self.generate_random_password()
        config['password'] = password

        max_tries = 3
        while True:
            max_tries -= 1
            if max_tries == 0:
                raise ServiceException('容器实例存储目录创建失败')
            volume_name = self.generate_random_volume()
            volume_path = f'{settings.DOCKER_VOLUME_ROOT}/redis/{volume_name}'
            if not os.path.exists(volume_path):
                break

        try:
            os.makedirs(volume_path)
            os.chmod(volume_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        except PermissionError:
            raise ServiceException('容器实例存储目录创建失败')

        self.generate_config_file(config, volume_path)

        try:
            image = self.docker_client.images.get(self.image_tag)
        except docker.errors.ImageNotFound:
            raise ServiceException('存储资源类型镜像不存在')

        port = self.pick_random_port()
        if port == 0:
            raise ServiceException('宿主机暂无可用端口')

        command = 'redis-server /opt/redis.conf'
        options = dict(
            ports={'6379/tcp': port},
            volumes={
                volume_path: {'bind': '/opt', 'mode': 'rw'},
            },
            #auto_remove=True,
            detach=True,
            tty=True,
            stdin_open=True)
        container = self.docker_client.containers.create(image, command=command, **options)
        container.start()
        time.sleep(3)

        container = self.get(container.short_id)
        if ContainerStatus(container.status) == ContainerStatus.CREATED:
            raise ServiceException('容器实例启动失败')

        instance = ContainerInstance(
                    id=container.short_id,
                    name=container.name,
                    ports=container.ports,
                    status=ContainerStatus(container.status))

        connection = RedisConnection(
                        host=settings.DOCKER_HOST_IP,
                        port=port,
                        password=password)
        return instance, connection
