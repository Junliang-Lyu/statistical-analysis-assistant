#!/usr/bin/env bash
# Read-only audit. Run through an already trusted SSH connection, via stdin.
# Never sources, reads or prints .env.production; never calls compose config.
set -u
printf '\n== public deployment paths and file hashes ==\n'
for base in /opt/portfolio/current /opt/investment/current; do
  readlink -f "$base" || true
done
for file in /opt/portfolio/current/deploy/Caddyfile \
            /opt/portfolio/current/deploy/compose.yaml \
            /opt/investment/current/compose.invest.yaml \
            /opt/investment/current/invest.caddy \
            /opt/investment/bin/auto-deploy.sh; do
  if [ -f "$file" ]; then sha256sum "$file"; else printf 'MISSING %s\n' "$file"; fi
done
printf '\n== import directives only ==\n'
grep -nE '^[[:space:]]*import[[:space:]]' /opt/portfolio/current/deploy/Caddyfile || true
printf '\n== container states (no environment inspection) ==\n'
sudo -n docker ps --format '{{.Names}} | {{.Status}} | {{.Ports}}' || true
printf '\n== Caddy mounts, networks and project labels only ==\n'
ids=$(sudo -n docker ps -q --filter label=com.docker.compose.service=caddy) || ids=''
for id in $ids; do
  sudo -n docker inspect --format 'Name={{.Name}} Project={{index .Config.Labels "com.docker.compose.project"}} ConfigFiles={{index .Config.Labels "com.docker.compose.project.config_files"}}' "$id" || true
  sudo -n docker inspect --format '{{range .Mounts}}{{println .Source "->" .Destination "readonly=" (not .RW)}}{{end}}' "$id" || true
  sudo -n docker inspect --format 'Networks={{range $name, $value := .NetworkSettings.Networks}}{{$name}} {{end}}' "$id" || true
done
printf '\n== timer status and memory snapshot ==\n'
systemctl is-active investment-deploy.timer || true
sudo -n docker stats --no-stream --format '{{.Name}} | {{.MemUsage}}' || true
printf '\n== existing HTTPS baselines ==\n'
for url in https://jun-liang-lyu.com/en/ \
           https://jun-liang-lyu.com/api/health \
           https://invest.jun-liang-lyu.com/lab \
           https://invest.jun-liang-lyu.com/api/health \
           https://stats.jun-liang-lyu.com/api/health; do
  curl -sS --max-time 15 -o /dev/null -w '%{http_code} %{url_effective}\n' "$url" || true
done
printf '\nAudit ended. No files, services, containers, DNS or secrets changed.\n'
