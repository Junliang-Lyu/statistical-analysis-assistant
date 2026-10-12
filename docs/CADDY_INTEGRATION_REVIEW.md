# 共享 Caddy 接入调查与待审批方案

日期：2026-10-12。依据仅为本地文件；没有连接服务器，不能确认线上文件与本地完全相同。本次不部署、不修改 self_web / Investment Lab、不读取密钥、不操作 DNS、不提交或推送。

## 1. 当前管理方式

| 项目 | 本地来源 | 按发布说明推定的服务器位置 / 容器位置 |
| --- | --- | --- |
| 主 Caddy 配置 | self_web/deploy/Caddyfile | /opt/portfolio/current/deploy/Caddyfile → /etc/caddy/Caddyfile，只读单文件挂载 |
| 主站静态内容 | self_web/deploy/compose.yaml | 相邻 site 目录 → /srv/site，只读挂载 |
| 投资站点配置 | investment-lab/deploy/compose.invest.yaml | /opt/investment/current/invest.caddy → /etc/caddy/sites/invest.caddy |
| 投资静态内容 | 同上 | /opt/investment/current/site → /srv/invest |
| HTTPS / Caddy 状态 | self_web/deploy/compose.yaml | caddy_data → /data；caddy_config → /config，实际卷名取决于现有 Compose project |
| 基础网络 | self_web/deploy/compose.yaml | Caddy 连接 edge、backend；backend 为 internal 网络 |
| 投资网络 | compose.invest.yaml | 增加 invest 网络，连接 Caddy 和 investment-api |

主 Caddyfile 已有 `import /etc/caddy/sites/*.caddy`，但主 Compose 没有挂载整个 sites 目录；投资 override 只挂载 invest.caddy。因此该 import 不会自动发现主机任意目录的新文件。

投资发布脚本 `deploy/server/auto-deploy.sh` 的 `dc()` 使用两份文件：主站 compose.yaml + 投资 current/compose.invest.yaml。`switch_to()` 每次运行 `up -d`，然后 `up -d --force-recreate caddy`；失败回滚也走同一路径。原因是 Docker 创建容器时解析 current 的挂载路径，单纯切换软链接不能更新已存在的挂载。

主站 DEPLOYMENT.md 描述发布时切换 /opt/portfolio/current，再执行 Compose up；并未证明线上已有自动拉取器。本地 GitHub deploy.yml 发布到 GitHub Pages，与 Lightsail 不同，不能当作 Lightsail 自动发布证据。只有服务器只读核查获准后，才能确认实际 project 名、版本、挂载和定时器。

## 2. 会不会丢入口

- 手工 docker network connect、临时挂载、仅通过 Caddy API 加路由：不能保证下次重建保留，不采用。
- 只准备 stats.caddy：无挂载和共享网络时，主 Caddy 无法使用它。
- 加一个第三 Compose override，但不改变发布命令：投资脚本显式只带两份文件，第三份不会自动读取；普通 compose.override.yaml 也不会在显式 -f 场景下自动参与。
- 推荐方案：把统计入口的挂载和网络写进主站基础 compose.yaml，再给主 Caddyfile 加独立 import。投资 override 添加的 invest 挂载/网络不会覆盖不同目标的统计挂载/网络。
- 之后投资发布与投资回滚仍使用这份基础配置，统计入口得以保留。主站新版本必须保留同样的基础改动；回滚到接入之前的主站配置会丢入口，因此不得直接回滚到未准备的旧基础配置。

## 3. 最小方案及边界

建议只为 Caddy 增加：

1. `/opt/stats/gateway` → `/etc/caddy/stats` 的只读目录挂载；目录独立于 stats/current 软链接。只放公开站点配置，不放 .env、密钥或数据。
2. 主 Caddyfile `import /etc/caddy/stats/*.caddy`，保留现有投资 import 和主站路由。
3. Caddy 与 stats-api 共用预先创建的 external 网络 stats_edge。两份 Compose 都声明 external，停止统计项目不会删除该共享网络。stats-api 不加入 backend 或 invest 网络，不开放主机端口。

统计服务由独立 Compose project `stats` 管理，镜像更新不重建主 Caddy。固定站点配置放 gateway/stats.caddy，应用版本放 releases/<ID>，current 仅记录通过检查的版本。今后修改 gateway 规则须单独审查；发布包里的 stats.caddy 不会自动被拉取器安装到 gateway。

**不必修改 Investment Lab 自动发布脚本或应用。必须经确认后修改主站基础配置，并保证主站发布/回滚流程携带这两处改动。** 若要求主站基础配置也完全不动，则当前重建方式下无法可靠长期新增入口；不能宣称已经解决。

一次性的 Caddy 重建会使三个站点短暂中断；配置错误可能同时影响三个入口。external 网络或目录未创建时基础服务启动会失败。顺序必须是先准备目录/网络和统计服务，再验证配置，最后重建 Caddy。小实例的 512 MB 统计容器上限也需要上线时检查实际余量；现有服务配置的最大内存之和不是可同时占用的容量保证。

## 4. 文件列表与影响

| 文件 | 本次状态 | 经批准后用途 / 影响 |
| --- | --- | --- |
| stats/deploy/compose.stats.yaml | 本地增加 external: true | 独立统计服务；前置要求是 stats_edge 已存在 |
| stats/deploy/stats.caddy | 保留现有草案 | stats 子域名转发 stats-api:8082；安全响应头及转发 IP |
| stats/deploy/proposals/self-web-stats.patch | 新增，未应用 | 主站两个文件的最小补丁；不包含投资代码 |
| self_web/deploy/Caddyfile | 未修改，仅补丁提议 | 新增统计目录 import，不改主站/投资规则 |
| self_web/deploy/compose.yaml | 未修改，仅补丁提议 | 只为 Caddy 增加目录挂载与外部网络声明，不改已有服务/卷 |
| stats/docs/RELEASE_AND_ROLLBACK_CHECKLIST.md | 新增 | 包内容、上线验收、回滚边界与检查 |
| stats/docs/CADDY_INTEGRATION_REVIEW.md | 新增 | 证据、风险、文件影响和审批顺序 |
| Investment Lab 全部文件 | 未修改，无拟议修改 | 继续使用原发布脚本 |

服务器待批准的新增位置：/opt/stats/{gateway,bin,releases,state}、/opt/stats/current、/opt/stats/.env.production（权限 600，密钥不进入任何包）；以及 stats 专用 systemd 单元（初期仅校验，不启用安装）。主站当前配置需通过受控主站发布落地，不能只手改服务器当前版本后忘记仓库。

## 5. 上线步骤（仅计划，本次不执行）

- [ ] 用户确认补丁范围、短暂共享网关中断、DNS 和私有模型配置方式。
- [ ] 获准后先只读对照线上 Caddy、Compose project、路径、计时器与本地版本；不输出环境文件内容。任何差异先修订计划。
- [ ] 固定当前主站/投资版本和验收基线，备份公共网关配置；协调一次性网关维护与现有自动发布，避免并发操作。
- [ ] 本地应用/审核主站补丁，准备包含补丁的主站发布配置和可回滚配置；不修改投资发布流程。重新构建统计包，旧 20261012T204229Z 包不包含本次 external 网络改动，不可冒充最新版。
- [ ] 用户在 Cloudflare 添加 A：名称 stats，值为已有 Lightsail 静态 IPv4，初期 DNS only，TTL Auto；实际 IP 尚未核查。不创建指向错误主机的 AAAA。
- [ ] 经批准在服务器仅准备 stats 目录和 stats_edge；创建私有 .env.production，显式核对模型与价格上限，不复用/输出已有项目密钥。
- [ ] 服务器接收/拉取已验证统计包并 docker load，不拉源码构建。先启动 stats-api，容器内健康检查通过。
- [ ] 安装已审核的 gateway/stats.caddy，验证三站合并 Caddy 配置；通过主站基础配置更新，只重建已有 Caddy，不执行整个栈 force-recreate。
- [ ] 完成三站 HTTPS、四方法、解释追问、2025 重算、限流及停止场景验收；验证按投资原有两文件合并重建时仍保留统计挂载/网络。实际投资发布需另行授权，不能为了测试而发布投资版本。
- [ ] 核对回滚演练后才允许统计自动安装模式；最后发布个人网站 Lab 链接。配置有误先回滚共享网关，不更改投资镜像/数据。

参考官方语义：Compose 合并 https://docs.docker.com/reference/compose-file/merge/ ，external 网络 https://docs.docker.com/reference/compose-file/networks/ ，Caddy import https://caddyserver.com/docs/caddyfile/directives/import 。

## 6. 本次验证

- 补丁只在统计仓库的忽略目录内应用到主站配置副本；对原主站执行的 `git apply --check --ignore-space-change` 通过，未实际应用。该选项处理 Windows CRLF 与补丁 LF 的上下文差异。
- 使用纯占位环境值、`--env-file NUL` 和 `--no-env-resolution` 校验 Compose，不加载任何真实 .env。确认原投资 override 合并后保留五个关键挂载及 edge/backend/invest/stats_edge 四个网络；统计服务仍独立且无主机端口。
- 临时本地 Caddy 容器同时读取主站副本、原投资站点规则和统计草案，`caddy validate` 通过；没有启动公网服务。格式与冗余转发头警告不阻止解析。
- 两项发布包安全检查测试通过，git diff --check 通过；本次未改应用逻辑，无额外依赖、提交、推送或 Release。
- 这些结果证明本地配置可合并/解析，不代表已经验证线上部署、证书签发或生产重建。
