# 线上 Caddy 只读核对结果

来源：用户通过 Lightsail 浏览器 SSH 提供的 2026-10-12 终端输出；助手未建立 SSH 连接。未读取私钥、API Key 或 .env.production 内容，未执行任何变更。

## 已确认

- 主站 current：/opt/portfolio/releases/20260928T045946Z。
- 投资 current：/opt/investment/releases/20261011T164215Z。
- 用户贴出的主站 Caddyfile 与 compose.yaml 均与本地 self_web 文件内容一致（归一化 CRLF/LF 后逐字比较）。
- 运行中 Caddy：deploy-caddy-1，Compose project 为 deploy。
- 当前 Caddy 挂载：主站 current/deploy/Caddyfile → /etc/caddy/Caddyfile，主站 site → /srv/site，投资 current/invest.caddy → /etc/caddy/sites/invest.caddy，投资 site → /srv/invest。
- Caddy 状态卷为 deploy_caddy_data 和 deploy_caddy_config；网络为 deploy_backend、deploy_edge、deploy_invest。
- 主站配置保留 sites/*.caddy import，目前无 stats import、统计目录挂载或 stats_edge。
- 投资 API 与 PostgreSQL 显示 healthy；registry 正在运行。只有 Caddy 发布主机 80/443；API 的 8080/8081 和数据库 5432 没有主机映射。docker ps 中 2019/tcp 只是容器端口，不能误说成对公网发布。
- 首次粘贴出现 bracketed-paste 控制字符，后续完整重跑成功；不是 readlink 实际不存在。

## 第二轮核对已完成

- 已安装脚本 STACK 为 /opt/portfolio/current/deploy，dc() 显式合并主站基础和投资 current/compose.invest.yaml，switch_to() 含 --force-recreate caddy；timer 为 active。
- 容器内配置和主机文件 SHA-256 均为 06c05d59aba9c97be6b35eeec6d65968142641aada387de267b125754e712424。
- .env.production 为 ubuntu:ubuntu 所有的普通文件，权限 664。未读取内容；该权限允许其他本机用户读取，建议经批准改为 600。新主站发布必须保留其可用路径，否则现有投资脚本的 .env 路径会失效。

## 后续命令必须采用的实际边界

任何获批的共享 Caddy 操作必须显式使用 --project-name deploy、主站基础 compose 加投资 current/compose.invest.yaml，定向操作 caddy；统计操作显式使用 --project-name stats，仅操作 stats-api。不能采用整个主站栈 down/up 或 force-recreate 全部服务。主站两配置文件先提交，再经受控主站发布落地。主站旧 release 作为回滚点保留，投资 current/镜像/应用/脚本均不修改。

在最后的只读核对及实施命令批准之前，不应用补丁、创建网络、切换 current、重启 Caddy、改 DNS 或发布。
