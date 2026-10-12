# 本地待上线发布包

2026-10-12：用户批准了本地修改、单独提交和发布包准备；没有批准本轮 GitHub Release 上传或服务器变更。下列产物已在本地生成并验证，尚无可用公开下载地址。

## 主站配置

- 本地主站提交：ec334707bc009c45aa30fa31d57da34189830174。
- 恰好两文件：deploy/Caddyfile、deploy/compose.yaml；新增 12 行。
- 主站其他四个已修改 MDX 与一个未跟踪设计文档保留，未包含在提交或包中。
- ID：20261012T213750Z。
- 文件：deploy/release/portfolio-config-20261012T213750Z.tar.gz 和 .sha256。
- SHA-256：724dc582f561067dca55f5a7e81ca6aeffbcda2ac6933a291f00fafd29a0224b。
- 包内四文件：deploy/Caddyfile、deploy/compose.yaml、manifest.json、release.txt。manifest 记录源提交及两个配置的哈希；无 .env、密钥或网站未提交内容。
- 原部署边界检查通过；提交内容与此前验证的三站合并配置一致。只做配置发布，主站静态产物和 registry 镜像复用现有已上线版本，不在服务器构建。

## 统计服务

- ID：20261012T213712Z；镜像 stats-api:20261012T213712Z。
- 文件：deploy/release/stats-release-20261012T213712Z.tar.gz 和 .sha256。
- SHA-256：df100a00a0a07be30564db4d31281cf6a4ed198fa73c46ba7cf53b6cdcd2dcdb。
- 大小约 142.1 MiB。
- 包包含五个白名单文件，compose 的 stats_edge 为 external，无 ports；stats.caddy 与审核草案一致。
- 85 tests passed；镜像四方法、解释型追问复用、Origin 拒绝、非 root / 文件边界冒烟通过；SHA 和安全 archive 验证通过。

## 接下来待批准

1. 上传主站配置提交及两个已验证发布包到对应 GitHub 仓库/Release，使服务器可通过固定地址拉取。不得误触发主站 Pages 发布，不触发 Investment 发布。
2. 提供填好上述固定版本及下载地址的线上命令，再单独批准服务器操作。所有命令沿用 project deploy / stats，不改 Investment 应用或逻辑。
3. DeepSeek 私有配置与模型价格尚未配置到服务器；不能把基础设施上线说成真实模型分析已可用。此阶段不索取或写入密钥。

当前配置包不含服务器 bootstrap 脚本；这些必须单独审核和交付，不能让拉取器假定包内存在它们。两个发布包的本地目录已被 Git 忽略，不提交大镜像文件。
