# Docker 部署

[中文首页](../README.md) | [English](DOCKER.md)

适用于已安装 Docker Engine 和 Docker Compose v2 的 Linux 服务器。镜像自带 Python、Node.js、Git 和 Codex CLI，
不需要在宿主机另外安装 Python 或 Codex。默认使用 Codex 0.159.2，以普通用户运行。
构建需要访问镜像仓库、Debian、npm 和 Python 软件源，运行时需要访问自己的模型服务。
建议从 2 核、4 GB 内存、20 GB 空闲磁盘起步，项目依赖和构建可能需要更多资源。

Codex 的 Linux 沙箱需要非特权用户命名空间。Compose 使用仓库提供的 seccomp 配置，
在 Docker 默认规则基础上允许 bubblewrap 创建内部沙箱；容器仍以普通用户运行、移除全部容器能力并禁止提权。
部署需保留 `deploy/seccomp-codex.json`。若宿主机内核或 AppArmor 禁止用户命名空间，需先由服务器管理员配置支持。

**使用网页前，仍需先在容器内配置好 Codex 登录或模型服务，确认 Codex 能正常对话。**
宿主机上已有的 Codex 登录不会自动进入容器；模型账号、密钥和额度由使用者自己提供。

## 一条命令部署

已安装 Git、Docker 和 Compose v2（需支持 `up --wait`）时，复制这一行：

```sh
git clone https://github.com/luxunhe-wq/codex-.git codex-web && cd codex-web && bash deploy.sh
```

已经下载项目的用户，只需在项目目录运行 `bash deploy.sh`。脚本会：

1. 自动准备 `.env.docker` 和运行环境。
2. 引导选择填写模型 API、登录 Codex，或导入已有的 `config.toml` / `auth.json`。
3. 提示创建网页账号，然后后台启动服务并显示访问地址。

填写 API 时，需要自己的厂商地址、模型名称和 API 密钥，服务需支持 Codex 使用的 Responses API。
密钥输入不会显示，也不会写入项目源码、命令参数或镜像，只保存在私有数据卷里。
导入操作只读取你选择的配置和登录文件，不导入历史、插件或宿主机环境变量；若配置依赖环境变量密钥，建议选择填写 API。
从自定义 API 切换到 Codex 登录时，旧配置会备份到数据卷内的 `config.before-login.toml`，避免继续使用旧模型服务。
配置完成后，在网页发送一条测试消息确认模型连接正常。

再次执行 `bash deploy.sh` 会复用配置、账号和数据。常用操作也可以通过脚本完成：

```sh
bash deploy.sh status       # 查看状态
bash deploy.sh stop         # 停止服务，保留数据
bash deploy.sh              # 再次启动
bash deploy.sh configure    # 修改模型配置
bash deploy.sh logs         # 查看日志
```

首次下载失败或很慢时，可执行 `bash deploy.sh --mirror` 使用 ECR Public、Berkeley Debian 镜像和华为云 Python 软件源。
如已有本地镜像且想强制重新构建，使用 `bash deploy.sh build --mirror`。
这些选项不会修改宿主机的 Docker 或软件源配置。首次配置需交互终端，不能通过 `curl | bash` 输入配置。
英文引导使用 `bash deploy.sh --en`。

默认访问 `http://127.0.0.1:8080`。远程服务器使用下方的 SSH 转发，手机和公网访问见 HTTPS 部署章节。
脚本验证容器健康和 Codex 沙箱，模型登录、额度及服务连通性由实际对话验证。

## 手动部署（可选）

以下是引导脚本所封装的 Docker 操作，需要自行控制流程时使用：

```sh
git clone https://github.com/luxunhe-wq/codex-.git codex-web
cd codex-web
cp .env.docker.example .env.docker
docker compose --env-file .env.docker build

# 按提示在浏览器中完成自己的 Codex 登录。
docker compose --env-file .env.docker run --rm -it codex-web codex login --device-auth

# 先确认容器里的 Codex 能正常对话，然后退出 CLI。
docker compose --env-file .env.docker run --rm -it codex-web codex

# 创建网页管理员；按终端提示输入账号和密码。
docker compose --env-file .env.docker run --rm -it codex-web python /app/server.py --init-admin

# 后台启动网页。
docker compose --env-file .env.docker up -d
```

设备登录是否可用取决于账号。若使用自定义模型服务，请按下一节写入自己的 Codex 配置。
网页管理员密码和 Codex 登录相互独立。浏览器访问 `http://127.0.0.1:8080`，用刚创建的网页账号登录。
远程服务器可先建立 SSH 转发，再访问自己电脑的 8080 端口：

```sh
ssh -N -L 8080:127.0.0.1:8080 your-user@your-server
```

首次构建会下载基础镜像及依赖，耗时取决于网络；后续构建可复用缓存。
目前从源码本地构建镜像，没有需要登录的预构建镜像仓库。

若 Docker Hub 无法连接，可使用 Docker Official Images 在 Amazon ECR Public 上的基础镜像：

```sh
docker compose --env-file .env.docker build \
  --build-arg NODE_IMAGE=public.ecr.aws/docker/library/node:22-bookworm-slim
```

这只替换基础镜像来源，Debian、npm 和 Python 软件源仍需可访问。
Debian 软件源也可在构建时通过 `DEBIAN_MIRROR`、`DEBIAN_SECURITY_MIRROR` 参数指定；默认使用 Debian 官方源。
Python 软件源可通过 `--build-arg PIP_INDEX_URL=https://你的镜像源/simple` 指定，默认使用 PyPI。

## Codex 配置和项目文件

三个 Docker 数据卷分别保存：

| 容器路径 | 保存内容 |
| --- | --- |
| `/home/node/.codex` | Codex 配置、登录凭据和历史 |
| `/data` | 网页管理员、对话数据库和附件 |
| `/workspace` | 项目文件；也是默认工作目录 |

容器重建会继续使用这些卷。不要用 `docker compose down -v` 升级，它会删除数据卷。
不要同时让多个网页容器使用同一个 `/data`。

将自己的配置写入持久化 Codex 目录，例如：

```sh
docker compose --env-file .env.docker run --rm -T codex-web \
  sh -c 'umask 077; cat > "$CODEX_HOME/config.toml"' < /secure/path/config.toml
```

若已有登录文件，也可用相同方式写入 `$CODEX_HOME/auth.json`，将输入文件和目标文件改成对应名称。
只导入需要的配置与凭据，不要将真实密钥提交到 Git 或加入镜像。
配置中的文件路径必须在容器内存在。模型服务地址中的 `localhost` 指容器自身；
如模型网关在宿主机，需配置可从容器访问的地址。

可以将项目克隆到 `/workspace`，然后在网页中「添加文件夹」选择 `/workspace/项目名`：

```sh
docker compose --env-file .env.docker exec codex-web \
  git clone https://github.com/your-account/your-project.git /workspace/your-project
```

使用宿主机项目目录时，在 `.env.docker` 中将 `CODEX_WEB_UID` / `CODEX_WEB_GID` 改成 `id -u` / `id -g` 的结果，
再构建镜像。默认值均为 1000；运行用户应为普通用户。创建 `compose.override.yaml`：

```yaml
services:
  codex-web:
    volumes:
      - type: bind
        source: /home/your-user/projects
        target: /workspace
        bind:
          create_host_path: false
```

该目录需提前存在，且运行用户有读写权限。容器中使用 `/workspace` 路径。
已有数据卷的所有者不会随着镜像 UID/GID 自动改变；修改已有部署的用户 ID 时需同步处理卷权限。
不同项目需要的编译器、工具和依赖，可通过扩展 Dockerfile 安装。

## 查看运行状态

```sh
docker compose --env-file .env.docker ps
docker compose --env-file .env.docker logs --tail=100 codex-web
docker compose --env-file .env.docker exec codex-web python /app/server.py --check
```

健康检查验证网页服务，不代表模型登录或模型网络一定正常；先用容器里的 Codex 验证模型连接。
容器只开放宿主机本地端口；`.env.docker` 中的 `CODEX_WEB_PUBLISH_PORT` 可修改宿主机端口。

## 手机和公网访问

按照 [HTTPS 部署](DEPLOYMENT.md)在宿主机配置域名与 Caddy，反向代理到 `127.0.0.1:8080`。
在 `.env.docker` 中设置：

```dotenv
CODEX_WEB_ALLOWED_HOSTS=localhost,127.0.0.1,codex.example.com
CODEX_WEB_SECURE_COOKIE=1
```

等待任务结束后执行 `docker compose --env-file .env.docker up -d`，再通过 HTTPS 域名访问。
启用 Secure Cookie 后，浏览器需使用 HTTPS 才能保持登录。网页管理员应通过前述终端命令提前创建。

## 备份和升级

等待所有任务结束后停止服务，导出三个卷。备份包含登录凭据，应按私有数据保存：

```sh
docker compose --env-file .env.docker stop
umask 077
mkdir -p backups
docker compose --env-file .env.docker run --rm -T codex-web tar -C /data -czf - . > backups/web-data.tar.gz
docker compose --env-file .env.docker run --rm -T codex-web tar -C /home/node/.codex -czf - . > backups/codex-config.tar.gz
docker compose --env-file .env.docker run --rm -T codex-web tar -C /workspace -czf - . > backups/projects.tar.gz
git pull --ff-only
docker compose --env-file .env.docker build
docker compose --env-file .env.docker up -d
```

升级保持相同的项目目录和 Compose 项目名称，使 Compose 继续找到原数据卷。
回滚需同时恢复对应代码、镜像和完整数据备份。
