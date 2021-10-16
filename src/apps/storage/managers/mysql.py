# coding=utf-8

import os
import stat
import time
from configparser import ConfigParser
import docker

from framework.conf import settings
from framework.exception import ServiceException
from .base import BaseManager
from ..models.container import ContainerInstance, ContainerStatus
from ..models.connection import MySQLConnection


class MySQLManager(BaseManager):

    image_tag = 'mysql:latest'

    def info(self, container_id: str):
        container = self.get(container_id)
        config_path = None
        for item in container.attrs['Mounts']:
            if item['Destination'] == '/etc/mysql/my.cnf':
                config_path = item['Source']
                break
        if config_path is None:
            raise ServiceException('容器实例中未发现配置文件')

        parser = ConfigParser()
        parser.read(config_path)
        config_info = {}
        for section in parser.sections():
            config_info[section] = dict([
                (key, value.strip("'").strip('"'))
                for key, value in parser[section].items()
            ])

        return config_info

    def generate_config_file(self, config: dict, volume_path: str):
        template_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir, 'templates'))
        parser = ConfigParser()
        parser.read(f'{template_dir}/my.cnf')
        parser.set('mysqld', 'character-set-server', config['charset'])
        parser.set('mysqld', 'binlog_format', config['binlog_format'])
        with open(f'{volume_path}/my.cnf', 'w') as fp:
            parser.write(fp)

    def create(self, config: dict = dict()):
        password = self.generate_random_password()

        max_tries = 3
        while True:
            max_tries -= 1
            if max_tries == 0:
                raise ServiceException('容器实例存储目录创建失败')
            volume_name = self.generate_random_volume()
            volume_path = f'{settings.DOCKER_VOLUME_ROOT}/mysql/{volume_name}'
            if not os.path.exists(volume_path):
                break

        self.generate_config_file(config, volume_path)

        try:
            os.makedirs(f'{volume_path}/data')
            os.chmod(f'{volume_path}/data', stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            os.makedirs(f'{volume_path}/logbin')
            os.chmod(f'{volume_path}/logbin', stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
        except PermissionError:
            raise ServiceException('容器实例存储目录创建失败')

        try:
            image = self.docker_client.images.get(self.image_tag)
        except docker.errors.ImageNotFound:
            raise ServiceException('存储资源类型镜像不存在')

        port = self.pick_random_port()
        if port == 0:
            raise ServiceException('宿主机暂无可用端口')

        options = dict(
            ports={'3306/tcp': port},
            volumes={
                f'{volume_path}/my.cnf': {'bind': '/etc/mysql/my.cnf', 'mode': 'ro'},
                f'{volume_path}/data': {'bind': '/mysql/data', 'mode': 'rw'},
                f'{volume_path}/logbin': {'bind': '/mysql/logbin', 'mode': 'rw'},
            },
            environment={'MYSQL_ROOT_PASSWORD': password},
            #auto_remove=True,
            detach=True,
            tty=True,
            stdin_open=True)
        container = self.docker_client.containers.create(image, **options)
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

        connection = MySQLConnection(
                        host=settings.DOCKER_HOST_IP,
                        port=port,
                        username='root',
                        password=password)
        return instance, connection
