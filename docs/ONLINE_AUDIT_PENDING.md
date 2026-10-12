# 线上只读核对：等待可信连接

2026-10-12：用户已授权只读核对线上配置，但任何修改/部署仍待单独批准。

主站 A 记录当前解析为 3.90.182.103。DNS 不能证明主机身份或服务器文件状态。使用严格主机指纹校验、非交互认证尝试连接 ubuntu@3.90.182.103，被 SSH 拒绝：未找到已验证的 ED25519 主机指纹。未绕过校验，未写入 known_hosts，未读取私钥或 .env。当前无法确认线上与本地一致。

已准备 deploy/proposals/audit-shared-caddy.sh。取得用户此前已验证的 SSH 连接方式后，通过 SSH stdin 执行，不上传文件。它仅读取公开配置哈希、current 指向、import 行、容器挂载/网络/项目标签、定时器状态、内存快照和 HTTPS 状态；不 source 环境文件，不使用可能展开密钥的 compose config，不输出容器 Env。

执行形式（不是已执行命令；TRUSTED_SSH_TARGET 必须由已验证连接确定）：

```powershell
Get-Content -Raw -Encoding utf8 deploy/proposals/audit-shared-caddy.sh | ssh -o BatchMode=yes -o StrictHostKeyChecking=yes TRUSTED_SSH_TARGET 'bash -s'
```

比对哈希时必须处理 Windows CRLF 与 Linux LF；字节哈希不一致不能直接判定配置有实质差异。若有差异，再请求只读取两份公开配置的内容进行逐行对比，仍不读取 .env。运行容器实际挂载应指向已核对文件；不能只看 current 指针就认定正在使用它。

核对通过后才生成最终实施命令，必须使用实际 Compose project、路径、版本号和健康 URL。主站 /api/health 可能在现有配置中未启用；如非 200，应记录真实基线及原有支持的健康接口，不能为接入统计而擅自修改主站 API。统计服务上线前不存在是预期基线，不可当成三个服务当前均健康。

本轮从本机只读检查 HTTPS：主站 /en/ 与 /api/health 均 200；投资 /lab 与 /api/health 均 200。统计 /api/health 连接失败，尚未验证可用。仅检查状态与证书连接，不调用模型、不输出响应体；这些结果不能证明线上配置文件与本地一致。

待批准的变更范围仍只有：主站 Caddyfile 的 stats import、主站基础 compose 的独立目录挂载与外部网络、统计独立后端。主站这两处必须提交并随受控主站发布落地；Investment Lab 应用和自动发布逻辑不改。普通静态内容不采用该接入流程。

本轮不生成带未核实 project 名称的可执行生产变更命令，不修改 self_web，不提交或推送，不发布，不操作 DNS，不写入秘密。
