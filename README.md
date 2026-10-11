# Codex Web Community

简体中文 | [English](docs/README.en.md) · [Docker 部署](docs/DOCKER.zh-CN.md) · [HTTPS 部署](docs/DEPLOYMENT.md) · [安全说明](SECURITY.md)

这是一个独立社区项目，让你在 Linux 上通过浏览器操作自己的 Codex。
不是 OpenAI 官方客户端，也不提供模型账号、API 密钥或免费额度。

## 使用前：先安装并配置好 Codex

**使用网页版之前，必须先配置好 Codex CLI（命令行应用），确认它能正常对话。**
原生部署需在同一 Linux 服务器、同一运行用户下安装并配置 Codex；Docker 镜像已包含 Codex CLI，需在容器内完成登录或模型配置。

1. 安装支持 `codex app-server --stdio` 的 Codex CLI，确认终端能执行 `codex --version`。
2. 完成自己的 Codex 登录，或配置受支持的模型服务，并确保服务器能连接该模型服务。
3. 在同一用户的终端运行 `codex`，发送一条消息，确认能正常收到回复，再安装和启动网页。

网页版调用服务器上的 Codex，沿用该用户的 Codex 配置。只在个人电脑上安装 Codex，不能代替服务器上的配置。
网页管理员账号与 Codex 登录相互独立；创建网页账号不会自动登录 Codex，也不会提供模型额度。
已有可正常使用的 Codex，在下载本项目后即可选择 Docker 或原生部署；Codex 安装和登录命令见下文。

## 运行环境

- 推荐 Ubuntu 24.04 LTS、Python 3.11/3.12；代码支持 Python 3.9 及以上。
- 建议从 2 核、4 GB 内存、20 GB 空闲磁盘起步。大型项目构建、依赖和附件需要更多空间。
- 配置支持 `codex app-server --stdio` 的 Codex CLI，并完成自己的登录或模型配置；Docker 模式在容器内配置。
- 本项目验证过 Codex 0.159.2；其他版本应先验证兼容性，不保证所有版本均可用。
- 使用远程模型无需 GPU。通过 npm 安装 Codex 才需要 Node.js，网页服务自身不依赖 Node.js。
- 使用普通 Linux 用户，准备项目所需的 Git、编译器、Node.js 或其他构建工具。
- 通过 npm 安装 Codex 时建议使用仍受支持的 Node.js LTS（22 或更新版本）。
- 服务器需要能通过 HTTPS 访问 GitHub、Python/npm 软件源及自己的模型服务；浏览器需要能访问网页服务。

## 下载项目

使用普通 Linux 用户，在准备存放项目的目录运行：

```sh
sudo apt update
sudo apt install git python3 python3-venv
git clone https://github.com/luxunhe-wq/codex-.git codex-web
cd codex-web
```

也可以[下载 ZIP 压缩包](https://github.com/luxunhe-wq/codex-/archive/refs/heads/main.zip)后解压；建议使用 Git 下载，方便后续升级。

## 安装并配置 Codex

以下是原生安装步骤。使用 Docker 可跳过宿主机上的 Codex/Python 安装，直接按下一节在容器内配置。

如果当前 Linux 用户已经能正常使用 Codex，可以跳过安装。否则先安装 Node.js LTS 和 npm，
再将 Codex 安装到当前用户自己的目录：

```sh
node --version
npm --version
npm install -g --prefix "$HOME/.local" @openai/codex
export PATH="$HOME/.local/bin:$PATH"
codex --version
codex login
codex login status
```

后续终端也需要将 `$HOME/.local/bin` 加入 PATH。没有浏览器的服务器可尝试 `codex login --device-auth`，
按照提示在其他设备完成登录；是否可用取决于账号。也可以使用自己已有的、受支持的模型服务配置。
先在终端运行 `codex` 确认能正常对话，再安装网页服务。
网页管理员密码和 Codex 登录是两套独立认证；仅安装本项目不能获得模型使用权限。
最新安装与登录选项以[官方 CLI 文档](https://developers.openai.com/codex/cli/)为准，以上 CLI 参数已用 0.159.2 核对。

## Docker 部署

已安装 Docker Engine 和 Docker Compose v2 的 Linux 服务器，可直接构建镜像。镜像包含 Python、Node.js 和 Codex CLI，
对话附件、Codex 登录配置和项目文件使用持久化数据卷保存。

在下载的项目目录内运行：

```sh
cp .env.docker.example .env.docker
docker compose --env-file .env.docker build
docker compose --env-file .env.docker run --rm -it codex-web codex login --device-auth
# 先用容器中的 Codex 验证能正常对话，再退出。
docker compose --env-file .env.docker run --rm -it codex-web codex
docker compose --env-file .env.docker run --rm -it codex-web python /app/server.py --init-admin
docker compose --env-file .env.docker up -d
```

浏览器访问 `http://127.0.0.1:8080`。Docker 模式不必运行下方的原生安装命令。
自定义模型服务、项目目录挂载、HTTPS、备份和升级见[完整 Docker 说明](docs/DOCKER.zh-CN.md)。

## 原生安装并启动网页

在下载的 `codex-web` 目录内，以普通用户运行：

```sh
python3 scripts/install.py --no-service
.venv/bin/python server.py --init-admin
.venv/bin/python server.py --check
.venv/bin/python server.py
```

安装脚本会建立 `.venv`、安装 Python 依赖并创建权限为 600 的 `.env`；不覆盖已有配置。
本地打开 `http://127.0.0.1:8080`。远程服务器可以先通过 SSH 转发访问：

```sh
ssh -N -L 8080:127.0.0.1:8080 your-user@your-server
```

在浏览器中访问本机 8080 端口。管理员密码通过终端提示输入，不出现在命令参数里。
本机未配置代理时也可通过本地网页创建管理员；非本机来源以及配置了 HTTPS/域名的部署禁止网页注册，必须使用 `--init-admin`。
手机或公网访问请参考 [HTTPS 部署](docs/DEPLOYMENT.md)。

## 常驻运行和升级

```sh
python3 scripts/install.py
systemctl --user status codex-web
journalctl --user -u codex-web -n 50
```

用户服务在退出 SSH 后继续运行或开机启动，可能需要管理员执行 `sudo loginctl enable-linger your-user`。
没有 systemd 用户服务的 Linux 环境可使用 `--no-service` 并自行配置进程管理器。
运行目录含空格也可使用；安装器生成对应路径的服务文件。

升级前先停止接受新任务，等待所有现有任务结束，停止服务，备份整个 `data/` 和自己的 Codex 历史：

```sh
systemctl --user stop codex-web
# 在服务停止后，将整个 data/ 复制到仓库外的备份目录。
git pull --ff-only
.venv/bin/python -m pip install -r requirements.txt
systemctl --user start codex-web
```

数据库迁移自动执行；新默认值仅用于新建数据库，已有项目和执行权限保留。
回滚需要恢复之前的代码版本、对应依赖和完整数据备份。

## 使用

- 中英文界面：登录页或「账号与设置 → 工作偏好 → 语言」中选择简体中文或 English，即时切换。
- 当前浏览器记住语言，刷新等待页也使用同一语言；切换保留草稿、附件、待回答问题及运行中的任务。
- 默认简体中文，语言选择独立于账号设置；对话内容、项目名称、文件正文和模型提供的工具说明保留原文。
- 文本和连续对话，实时回复、命令输出、审批、文件变更及停止任务。
- 持久保存项目文件夹和对话。长历史分页加载，刷新恢复上次对话。
- 登录保留 30 天，使用时自动续期；主动退出或修改密码撤销旧登录。
- 图片支持选择、粘贴、拖入、预览和重试；大图片尝试后台压缩，原图选项保留原始文件。
- 每条消息最多 8 个附件，图片每张最大 10 MiB，普通文件每个最大 25 MiB。
- 文件支持文本、代码、CSV、JSON、PDF、DOCX、XLSX、PPTX 及 ZIP 内的可读文本；原文件可下载。
- 文字 PDF 提取前 50 页；每个文件最多 12 万字符，单条消息提取文本总计最多 18 万字符。
- 扫描 PDF 每个文件最多渲染 4 页，每条消息最多提供 12 页图像。超限会注明，完整原文件保留。
- ZIP 只解析目录和文本，不解压到项目目录；上传文件不会作为程序执行。
- 思考时间仅按实际收到的可计量事件显示；上游不提供真实用时的条目会明确注明。
- 浅色、深色和系统主题；等待页与对话背景一致；手机输入区采用紧凑布局。

新安装默认项目内读写（`workspace-write`）、按需审批（`on-request`）。
可以在设置中开启完全访问，但登录用户能更改权限；这不是不同用户之间的隔离机制。
本项目仅有一个管理员账号，适合个人独立部署。不要让不可信的人使用同一实例。

## 配置

手动安装时将 [.env.example](.env.example) 复制为 `.env`；安装脚本会自动创建配置文件。
网页服务在启动时读取配置，可通过 `--env-file /absolute/path/to/config.env` 指定其他配置文件。

| 配置项 | 默认值或用途 |
| --- | --- |
| `CODEX_WEB_HOST` | `127.0.0.1`，默认仅监听本机 |
| `CODEX_WEB_PORT` | `8080` |
| `CODEX_WEB_DATA` | 项目内的 `data/`，保存账号数据库、对话和附件 |
| `CODEX_WEB_CWD` | 本仓库目录，新数据库的默认项目目录 |
| `CODEX_WEB_CODEX_BIN` | PATH 中的 `codex`，也可填写可执行文件的绝对路径 |
| `CODEX_HOME` | 沿用 Codex 默认配置目录，可选指定其他配置与历史目录 |
| `CODEX_WEB_ALLOWED_HOSTS` | 反向代理域名，以逗号分隔，不包含端口 |
| `CODEX_WEB_SECURE_COOKIE` | 默认 `0`；通过 HTTPS 反向代理访问时设为 `1` |

`.env` 不自动执行 shell，不展开 `$HOME` 或 `~`，路径请填写绝对路径。
环境变量优先于配置文件，命令行 host/port 优先于两者。
Codex 凭据保存在你自己的 Codex 配置目录，网页不会显示密钥。

后端使用 Python 和 SQLite，前端使用原生 HTML/CSS/JavaScript，无需前端构建。
网页服务通过本机 `codex app-server --stdio` 与 Codex 通信，浏览器通过 SSE 接收实时更新。

## 验证与发布

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m playwright install chromium
.venv/bin/python tests/browser_workspace.py
python3 scripts/check_release.py --staged
```

接口及模拟浏览器测试使用临时账号和数据库，不调用模型。`smoke_*.py` 使用真实模型，需自行明确运行。
Git 不应包含数据、凭据、聊天截图或附件；发布检查扫描全部 Git 暂存文件，只打印问题路径，不打印密钥。

本项目采用 [AGPL-3.0-only](LICENSE)，依赖声明见 [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md)。
