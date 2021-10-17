
# 题目

设计并实现一个简单的存储资源分配系统

实现一个服务，该服务可以接收用户端请求，为用户申请 MySQL 与 Redis 两类资源。分配给用户的资源实例必须是真实、可以连接使用的。用户可以通过接口查看分配给自己的资源配置信息。

- 服务以 HTTP REST API 的方式提供接口，部分示例接口：
  - 申请一个新的 MySQL/Redis 资源实例
  - 查看某个实例的配置信息
- MySQL、Redis 服务可以在服务端用 Docker 容器启动，也可以使用其他方式
- 分配出的不同实例之间需要避免端口等资源冲突
- 资源的连接、鉴权等信息应该随机生成，部分必须的信息
  - MySQL 连接地址、数据库名称、用户号、密码
  - Redis 连接地址、密码

加分项：

- 完整的项目架构图、项目安装、使用以及 README 文档
- MySQL 与 Redis 实例支持不同的个性化配置，比如：
  - MySQL 可以由用户设置数据库字符集
  - Redis 可以由用户设置数据最大占用空间

# 交付

## 项目架构图

[![](https://mermaid.ink/img/eyJjb2RlIjoiZ3JhcGggTFJcbiAgICBBKChDbGllbnQpKSAtLT58UkVTVCBBUEl8IEIoRmFzdEFQSSlcbiAgICBCIC0tPiBDKFJlZGlzIE1hbmFnZXIpXG4gICAgQiAtLT4gRChNeVNRTCBNYW5hZ2VyKVxuICAgIEMgLS0-IEVbRG9ja2VyIFNlcnZpY2VdXG4gICAgRCAtLT4gRVtEb2NrZXIgU2VydmljZV1cbiAgICBFIC0tPiBGW0ZpbGUgU3lzdGVtXVxuICAgICIsIm1lcm1haWQiOnsidGhlbWUiOiJkZWZhdWx0In0sInVwZGF0ZUVkaXRvciI6ZmFsc2UsImF1dG9TeW5jIjp0cnVlLCJ1cGRhdGVEaWFncmFtIjpmYWxzZX0)](https://mermaid-js.github.io/mermaid-live-editor/edit#eyJjb2RlIjoiZ3JhcGggTFJcbiAgICBBKChDbGllbnQpKSAtLT58UkVTVCBBUEl8IEIoRmFzdEFQSSlcbiAgICBCIC0tPiBDKFJlZGlzIE1hbmFnZXIpXG4gICAgQiAtLT4gRChNeVNRTCBNYW5hZ2VyKVxuICAgIEMgLS0-IEVbRG9ja2VyIFNlcnZpY2VdXG4gICAgRCAtLT4gRVtEb2NrZXIgU2VydmljZV1cbiAgICBFIC0tPiBGW0ZpbGUgU3lzdGVtXVxuICAgICIsIm1lcm1haWQiOiJ7XG4gIFwidGhlbWVcIjogXCJkZWZhdWx0XCJcbn0iLCJ1cGRhdGVFZGl0b3IiOmZhbHNlLCJhdXRvU3luYyI6dHJ1ZSwidXBkYXRlRGlhZ3JhbSI6ZmFsc2V9)

存储资源分配系统使用FastAPI构建Web服务，向前端提供REST API，后端基于系统中的Docker服务，进行Redis与MySQL存储资源实例的`查询/创建/删除`操作，容器实例的持久化数据保存在文件系统中。

## 下载项目代码

```bash
git clone https://github.com/liangyongxiong/bk-interview.git
```

## 代码目录结构

```
PROJECT/
 |- log/ (运行日志)
 |- src/
 |   |- apps/storage/
 |   |   |- managers/
 |   |   |   |- base.py (基类)
 |   |   |   |- mysql.py (MySQL资源管理器)
 |   |   |   |- redis.py (Redis资源管理器)
 |   |   |- models/
 |   |   |   |- connection.py (资源连接Model定义)
 |   |   |   |- container.py (容器实例Model定义)
 |   |   |- templates/
 |   |   |   |- my.cnf (MySQL配置文件模板)
 |   |   |   |- redis.conf (Redis配置文件模板)
 |   |- conf/
 |   |   |- config.py (项目配置文件)
 |   |- framework/ (项目框架基础模块)
 |   |- web/bk/
 |   |   |- conf/
 |   |   |   |- config.py (WEB服务配置文件)
 |   |   |- routers/
 |   |   |   |- mysql.py (MySQL资源REST API路由定义)
 |   |   |   |- redis.py (Redis资源REST API路由定义)
 |   |   |- schemas/
 |   |   |   |- base.py (基础HTTP数据Model定义)
 |   |   |   |- mysql.py (MySQL HTTP数据Model定义)
 |   |   |   |- redis.py (Redis HTTP数据Model定义)
 |   |   |- fastapi.py (FastAPI Builder)
 |   |- main.py (项目启动入口)
```

`src/conf/config.py`可配置docker服务的参数

```python
# docker服务连接
DOCKER_BASE_URL = 'unix:///var/run/docker.sock'
# docker实例磁盘根目录
DOCKER_VOLUME_ROOT = '/tmp/bk-interview'
# docker宿主机IP
DOCKER_HOST_IP = '127.0.0.1'
```

`src/web/bk/conf/config.py`可配置FastAPI的参数

```python
# 是否开启调试模式，开启后才能访问SwaggerUI接口文档
FASTAPI_DEBUG = True
# 是否对HTTP返回结果进行Gzip压缩
FASTAPI_ENABLE_GZIP = True
# 是否允许CORS访问
FASTAPI_ENABLE_CORS = True
```

## 运行环境约束

- 要求操作系统为Linux
- 要求系统已安装[Docker](https://docs.docker.com/engine/install/)
- 要求系统已安装[Python 3.9](https://www.python.org/downloads/release/python-397/)

## 下载docker镜像

```bash
docker pull redis:latest
docker pull mysql:latest
```

## 安装Python依赖包

```bash
pip install -r requirements.txt
```

## 启动资源分配系统服务

```bash
python src/main.py fastapi --domain bk
```

打开本地浏览器，访问 [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs) 即可查看基于 SwaggerUI 接口文档，并可在线触发 HTTP REST API

## HTTP REST API说明

### Redis

| 功能                 | 请求方式 | REST API                                          |
| -------------------- | :------: | ------------------------------------------------- |
| 获取资源实例列表     |   GET    | /api/storage/redis/instances                      |
| 创建资源实例         |   POST   | /api/storage/redis/instances                      |
| 获取资源实例配置信息 |   GET    | /api/storage/redis/instances/{instance_id}/config |
| 删除资源实例         |  DELETE  | /api/storage/redis/instances/{instance_id}        |

创建资源实例时，目前支持以下个性化配置：

- maxmemory：最大占用内存空间（单位：byte）
- maxclients：最大客户端连接数
- appendfsync：系统写盘模式，支持`always/everysec/no`

### MySQL

| 功能                 | 请求方式 | REST API                                          |
| -------------------- | :------: | ------------------------------------------------- |
| 获取资源实例列表     |   GET    | /api/storage/mysql/instances                      |
| 创建资源实例         |   POST   | /api/storage/mysql/instances                      |
| 获取资源实例配置信息 |   GET    | /api/storage/mysql/instances/{instance_id}/config |
| 删除资源实例         |  DELETE  | /api/storage/mysql/instances/{instance_id}        |

创建资源实例时，目前支持以下个性化配置：

- charset：服务端字符集，支持`utf8mb4/latin1`
- binlog_format：binlog格式，支持`STATEMENT/ROW/MIXED`

## 思考：系统可演进能力

1. 可使用持久化数据库，记录存储资源实例，支持分页查询
2. 使用Celery定时检测各容器实例的运行状态，通过注册回调或WebSocket方式，告知用户
