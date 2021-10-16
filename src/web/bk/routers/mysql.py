# coding=utf-8

from fastapi import APIRouter, Query

from apps.storage.managers.mysql import MySQLManager
from ..schemas.base import BaseResponse
from ..schemas.mysql import MySQLConfig


router = APIRouter(
    prefix='/api/storage/mysql',
    tags=['mysql'],
    responses={
        404: dict(description='Not found'),
    },
)


@router.get('/instances', response_model=BaseResponse, response_model_exclude_unset=True)
async def list_instances():
    instances = MySQLManager.instance().list()
    return dict(err=0, data={
        'total': len(instances),
        'instances': [instance.to_json() for instance in instances],
    })


@router.get('/instances/{instance_id}/config', response_model=BaseResponse, response_model_exclude_unset=True)
async def get_instance_config(instance_id: str = Query(None, regex=r'[0-9a-f]{12}')):
    config = MySQLManager.instance().info(instance_id)
    if config is None:
        return dict(err=1, msg='查询失败')
    return dict(err=0, data=config)


@router.post('/instances', response_model=BaseResponse, response_model_exclude_unset=True)
async def create_instance(config: MySQLConfig):
    config_dict = config.dict()
    instance, connection = MySQLManager.instance().create(config_dict)
    return dict(err=0, msg='创建成功', data={
        'instance': instance.to_json(),
        'connection': connection.to_json(),
    })


@router.delete('/instances/{instance_id}', response_model=BaseResponse, response_model_exclude_unset=True)
async def remove_instance(instance_id: str = Query(None, regex=r'[0-9a-f]{12}')):
    flag = MySQLManager.instance().remove(instance_id)
    if not flag:
	    return dict(err=1, msg='删除失败')
    return dict(err=0, msg='删除成功')
