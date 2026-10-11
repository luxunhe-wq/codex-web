#!/usr/bin/env bash
# Guided Docker deployment; never read credentials into shell variables or arguments.
set -Eeuo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
lang=zh-CN
action=start
build_args=()
for argument in "$@"; do
  case "$argument" in
    --en) lang=en ;;
    --mirror) build_args=(--build-arg NODE_IMAGE=public.ecr.aws/docker/library/node:22-bookworm-slim --build-arg DEBIAN_MIRROR=http://mirrors.ocf.berkeley.edu/debian --build-arg DEBIAN_SECURITY_MIRROR=http://mirrors.ocf.berkeley.edu/debian-security --build-arg PIP_INDEX_URL=https://repo.huaweicloud.com/repository/pypi/simple/) ;;
    --help|-h) echo 'Usage: bash deploy.sh [start|stop|status|logs|configure|build] [--en] [--mirror]'; exit 0 ;;
    start|stop|status|logs|configure|build) action=$argument ;;
    *) echo 'Usage: bash deploy.sh [start|stop|status|logs|configure|build] [--en] [--mirror]' >&2; exit 2 ;;
  esac
done
say() { if [[ $lang == en ]]; then echo "$2"; else echo "$1"; fi; }
fail() { say "$1" "$2" >&2; exit 1; }
trap 'say "部署未完成。修复上方错误后，重新运行同一命令即可继续。" "Deployment did not finish. Fix the error above and rerun the same command to resume." >&2' ERR
command -v docker >/dev/null || fail '请先安装 Docker Engine 和 Compose v2，再运行此命令。' 'Install Docker Engine and Compose v2 first, then rerun this command.'
docker compose version >/dev/null
docker info >/dev/null
compose() { docker compose --env-file .env.docker "$@"; }
setup() { compose run --rm -T codex-web python /app/scripts/docker_setup.py "$@"; }
interactive() {
  [[ -t 0 && -t 1 ]] || fail '首次配置需要交互终端，请直接在终端执行 bash deploy.sh。' 'Initial configuration needs a terminal. Run bash deploy.sh directly in a terminal.'
  compose run --rm -it codex-web "$@"
}
if [[ ! -e .env.docker ]]; then
  umask 077
  (set -o noclobber; cat .env.docker.example > .env.docker)
fi
case "$action" in
  stop) compose stop; exit ;;
  status) compose ps; exit ;;
  logs) compose logs --tail=100 -f codex-web; exit ;;
esac
image_setup_version=$(docker image inspect --format '{{ index .Config.Labels "io.codex-web.setup-version" }}' "${CODEX_WEB_IMAGE:-codex-web-community:local}" 2>/dev/null || true)
if [[ $action == build || $image_setup_version != 1 ]]; then
  say '正在构建运行环境，首次下载可能需要几分钟……' 'Building the runtime; the first download may take several minutes…'
  compose build "${build_args[@]}"
fi
if ! setup --idle; then
  fail '暂时无法继续：有任务正在执行，或数据库无法读取。请检查上方输出后重试。' 'Cannot continue: tasks are active or the database could not be read. Check the output above and retry.'
fi
if [[ $action == configure ]] || ! setup --has-config; then
  say '配置 Codex：1）填写模型 API  2）登录 Codex  3）导入已有配置' 'Configure Codex: 1) Model API  2) Sign in to Codex  3) Import existing configuration'
  [[ -t 0 && -t 1 ]] || fail '首次配置需要交互终端，请直接在终端执行 bash deploy.sh。' 'Initial configuration needs a terminal. Run bash deploy.sh directly in a terminal.'
  read -r -p "$(say '请选择 [1/2/3，默认 1]：' 'Choose [1/2/3, default 1]: ')" choice
  case "${choice:-1}" in
    1) interactive python /app/scripts/docker_setup.py --api --language "$lang" ;;
    2) interactive codex login --device-auth; setup --use-login ;;
    3)
      source_dir=${CODEX_HOME:-$HOME/.codex}
      read -r -p "$(say "Codex 配置目录 [$source_dir]：" "Codex configuration directory [$source_dir]: ")" supplied_dir
      source_dir=${supplied_dir:-$source_dir}
      files=()
      [[ ! -f "$source_dir/config.toml" ]] || files+=(config.toml)
      [[ ! -f "$source_dir/auth.json" ]] || files+=(auth.json)
      ((${#files[@]})) || fail '此目录没有 config.toml 或 auth.json。' 'No config.toml or auth.json found in this directory.'
      tar -C "$source_dir" -cf - -- "${files[@]}" | setup --import
      ;;
    *) fail '请选择 1、2 或 3，然后重试。' 'Choose 1, 2 or 3 and retry.' ;;
  esac
else
  say '已保留容器内的 Codex 配置。' 'Existing Codex configuration retained.'
fi
if ! setup --has-admin; then
  say '创建网页账号（与模型 API / Codex 登录相互独立）：' 'Create the web account (separate from model API / Codex authentication):'
  interactive python /app/server.py --init-admin
else
  say '已保留网页账号和数据。' 'Existing web account and data retained.'
fi
say '检查 Codex 沙箱并启动网页……' 'Checking the Codex sandbox and starting the website…'
compose run --rm -T codex-web codex sandbox -c 'sandbox_mode="workspace-write"' -- python -c 'print("Codex sandbox: OK")'
setup --idle || fail '有新任务正在执行，请等任务完成后重新运行。' 'New tasks are active. Finish them before rerunning deployment.'
up_args=(-d --wait --wait-timeout 90)
[[ $action != configure ]] || up_args+=(--force-recreate)
compose up "${up_args[@]}"
address=$(compose port codex-web 8080)
say "网页已启动：http://$address" "Website started: http://$address"
say '首次使用请在网页发送测试消息，确认模型配置和网络正常。' 'Send a test message in the website to verify model configuration and connectivity.'
say "远程访问：ssh -N -L ${address##*:}:127.0.0.1:${address##*:} 用户@服务器" "Remote access: ssh -N -L ${address##*:}:127.0.0.1:${address##*:} user@server"
