# 待批准的精确操作计划

本文件是操作提案，任何下面的修改命令都尚未执行。线上只读核对已完成，详见 ONLINE_CADDY_FINDINGS.md。

## 变更范围

1. 本地 self_web：仅应用 deploy/proposals/self-web-stats.patch 对两个配置文件的改动，单独提交这两个文件。不夹带现有未提交的网站内容，不改 Investment Lab。
2. 制作主站配置发布包，仅含已提交的 Caddyfile / compose.yaml、公开版本标识和 SHA-256；静态页面复用线上当前已发布产物，registry / PostgreSQL 镜像不变。服务器不构建源代码。
3. 重新制作统计发布包，含 external stats_edge 配置，公开发布后由服务器下载已验证产物。旧统计包不含本轮改动，不直接使用。
4. 主站版本目录切换后定向重建 Caddy；不重建 registry / PostgreSQL / investment-api，不修改投资 current、应用或自动发布脚本。
5. 权限修复独立审批：主站现有 .env.production 从 664 改为 600。仅修改元数据，不读取内容。

## A. 本地提交（待批准）

在 self_web 目录：

```powershell
git apply --check --ignore-space-change "C:/Users/ASUS/Desktop/学习/秋季2/7327AI agentic/statistical-analysis-assistant/deploy/proposals/self-web-stats.patch"
git apply --ignore-space-change "C:/Users/ASUS/Desktop/学习/秋季2/7327AI agentic/statistical-analysis-assistant/deploy/proposals/self-web-stats.patch"
git diff -- deploy/Caddyfile deploy/compose.yaml
git add deploy/Caddyfile deploy/compose.yaml
git diff --cached --name-only
```

必须确认暂存集合恰为这两个文件，才提交及发布。本地打包从该提交提取文件，不从混有其他未提交改动的工作目录打包。正式发布包生成后再提供它的固定 URL、ID 与独立校验值；此时没有这些产物，不能编造下载命令或把最新 Release 当成固定版本。

## B. 上线前基线（只读，可在变更开始前重跑）

```bash
for url in https://jun-liang-lyu.com/en/ https://jun-liang-lyu.com/api/health https://invest.jun-liang-lyu.com/lab https://invest.jun-liang-lyu.com/api/health; do
  curl --fail --silent --show-error --max-time 15 -o /dev/null -w '%{http_code} %{url_effective}\n' "$url" || break
done
readlink -f /opt/portfolio/current
readlink -f /opt/investment/current
```

四个 URL 必须均通过。记录投资 current、image ID，不读取容器 Env。

## C. 一次性准备（待批准；暂不执行）

```bash
sudo install -d -m 0755 /opt/stats/gateway /opt/stats/releases /opt/stats/bin
sudo install -d -m 0700 /opt/stats/state
if ! sudo docker network inspect stats_edge >/dev/null 2>&1; then
  sudo docker network create --driver bridge stats_edge
fi
```

已有 stats_edge 时不能无条件使用：核对网络是预期 bridge 且无其他无关容器。主站基础配置添加 external 网络后，如果网络不存在，启动会失败。统计 .env.production 由用户在独立私有步骤准备；助手不写入/索取/展示密钥，不从已有主站或投资文件提取模型配置。未配置模型时先以离线方式验收基础设施，不能声称真实分析已上线。

## D. 主站配置发布与 Caddy 切换（待批准）

固定发布产物下载、校验、解包命令，在 A 阶段完成后以实际 URL/ID补齐再审批；不使用未校验的 latest。在下面步骤之前，新的两个配置文件已放在新主站发布目录的 deploy/，并通过本地三站合并验证。

短暂暂停投资定时器仅是维护期运行状态变更，不改其逻辑。停止 timer 不会停止已在运行的 service，因此发现 service active 时必须恢复 timer 并退出，等待发布完成，不强行中断。

```bash
sudo systemctl stop investment-deploy.timer
if systemctl is-active --quiet investment-deploy.service; then
  sudo systemctl start investment-deploy.timer
  printf 'Investment deployment is running; abort maintenance.\n'
else
  printf 'No running Investment deployment; maintenance may proceed.\n'
fi
```

后续有 active 状态时不执行。新主站 release ID 由已审核的产物确定，不能直接运行下面缺少 NEW 的片段：

```bash
OLD=/opt/portfolio/releases/20260928T045946Z
# NEW 必须设为已核验主站发布目录，例如 /opt/portfolio/releases/<实际ID>
test "$(readlink -f /opt/portfolio/current)" = "$OLD"
test -d "$NEW/deploy"
test ! -e "$NEW/deploy/site"
sudo cp -a "$OLD/deploy/site" "$NEW/deploy/site"
test ! -e "$NEW/deploy/.env.production"
sudo ln "$OLD/deploy/.env.production" "$NEW/deploy/.env.production"
```

硬链接只新增文件名，不由助手读取秘密内容；原权限/所有权保持。两个名称初始指向同一 inode。投资脚本以后 sed -i 更新新路径可能产生独立文件，这是预期；后续回滚不得直接使用旧环境文件。旧 release 及其私有文件不能清理。若用户单独批准权限修复：`sudo chmod 600 "$NEW/deploy/.env.production"`（初始硬链接也会修正旧路径权限）。

统计镜像需先 docker load 并独立启动 stats-api，通过容器内部健康检查，再将审核的 stats.caddy 安装到 /opt/stats/gateway/stats.caddy。统计启动命令使用实际已验证镜像版本，由统计发布清单生成，固定 --project-name stats，仅 up stats-api；没有主机 ports。

验证候选网关（Compose 引擎按部署需要注入环境配置，不打印/读取其内容供助手分析；命令输出不可使用 compose config 展开环境）：

```bash
cd "$NEW/deploy"
sudo docker compose --project-name deploy --env-file .env.production -f compose.yaml -f /opt/investment/current/compose.invest.yaml run --rm --no-deps caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
```

通过后原子切换 current（临时链接不能已存在）：

```bash
test ! -e /opt/portfolio/current.stats-next
test ! -L /opt/portfolio/current.stats-next
sudo ln -s "$NEW" /opt/portfolio/current.stats-next
sudo mv -Tf /opt/portfolio/current.stats-next /opt/portfolio/current
cd /opt/portfolio/current/deploy
sudo docker compose --project-name deploy --env-file .env.production -f compose.yaml -f /opt/investment/current/compose.invest.yaml up -d --no-deps --force-recreate caddy
```

只重建共享 Caddy，因此三个入口可能短暂中断。失败立即进入回滚，不继续更新其他服务；无论成功或完成回滚，恢复 `sudo systemctl start investment-deploy.timer`，不执行 enable/disable，不改变开机设置。

## E. 验收与回滚（待批准）

重跑 B 的四 URL，再检查统计首页与 /api/health、/release.txt 和其版本；最初 TLS 申请允许短暂等待但必须有超时。随后四方法、解释追问、日期重算、会话隔离、限流/预算失败提示验收。真实模型验收必须在用户私有配置完成后进行。

主站网关发布失败回滚（NEW 仍指向这次候选目录，OLD仍是基线）：

```bash
test -f "$NEW/deploy/.env.production"
if ! test "$NEW/deploy/.env.production" -ef "$OLD/deploy/.env.production"; then
  sudo ln -f "$NEW/deploy/.env.production" "$OLD/deploy/.env.production"
fi
test ! -e /opt/portfolio/current.stats-rollback
test ! -L /opt/portfolio/current.stats-rollback
sudo ln -s "$OLD" /opt/portfolio/current.stats-rollback
sudo mv -Tf /opt/portfolio/current.stats-rollback /opt/portfolio/current
cd /opt/portfolio/current/deploy
sudo docker compose --project-name deploy --env-file .env.production -f compose.yaml -f /opt/investment/current/compose.invest.yaml up -d --no-deps --force-recreate caddy
sudo systemctl start investment-deploy.timer
```

上述 -ef 防护避免源/目标仍为同一 inode 时硬链接报错。恢复最新私有文件的路径关系，不查看或打印内容，避免回滚时恢复陈旧投资镜像设置。此次回滚撤销统计入口，但主站和投资必须恢复；外部网络和预算卷不删除。

本地 A 阶段已完成，固定产物见 RELEASE_CANDIDATES.md；公开下载地址尚未生成。经批准上传之后会填入真实 URL。未经最终批准，任何线上修改都不执行。
