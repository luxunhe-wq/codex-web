# Codex Web Community 中文说明

这是一个独立社区项目，让你在 Linux 上通过浏览器操作自己的 Codex。
不是 OpenAI 官方客户端，也不提供模型账号、API 密钥或免费额度。

## 运行环境

- 推荐 Ubuntu 24.04 LTS、Python 3.11/3.12；代码支持 Python 3.9 及以上。
- 建议从 2 核、4 GB 内存、20 GB 空闲磁盘起步。大型项目构建、依赖和附件需要更多空间。
- 本机安装支持 `codex app-server --stdio` 的 Codex CLI，并完成自己的登录或模型配置。
- 本项目验证过 Codex 0.159.2；其他版本应先验证兼容性，不保证所有版本均可用。
- 使用远程模型无需 GPU。通过 npm 安装 Codex 才需要 Node.js，网页服务自身不依赖 Node.js。
- 使用普通 Linux 用户，准备项目所需的 Git、编译器、Node.js 或其他构建工具。

## 安装

克隆仓库后进入目录，以普通用户运行：

```sh
sudo apt install python3-venv
codex --version
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
手机或公网访问请参考 [HTTPS 部署](DEPLOYMENT.md)。

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

配置项见根目录 [README](../README.md) 与 [.env.example](../.env.example)。
`.env` 不自动执行 shell，不展开 `$HOME` 或 `~`，路径请填写绝对路径。
环境变量优先于配置文件，命令行 host/port 优先于两者。
Codex 凭据保存在你自己的 Codex 配置目录，网页不会显示密钥。

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

本项目采用 [AGPL-3.0-only](../LICENSE)，依赖声明见 [THIRD_PARTY_NOTICES](../THIRD_PARTY_NOTICES.md)。
