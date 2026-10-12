#!/usr/bin/env bash
# One-time stats-only preparation. Does NOT start or enable the timer/service.
set -eu
[ "$(id -u)" = 0 ] || { echo 'Run as root after explicit server approval.'; exit 1; }
for tool in python3 docker curl; do command -v "$tool" >/dev/null; done
here=$(cd "$(dirname "$0")" && pwd)
[ ! -L /opt/stats ] || { echo '/opt/stats must not be a symlink'; exit 1; }
install -d -m 0755 /opt/stats /opt/stats/bin /opt/stats/releases
install -d -m 0700 /opt/stats/state
install -m 0755 "$here/auto_deploy.py" /opt/stats/bin/auto_deploy.py
install -m 0644 "$here/stats-deploy.service" /etc/systemd/system/stats-deploy.service
install -m 0644 "$here/stats-deploy.timer" /etc/systemd/system/stats-deploy.timer
systemctl daemon-reload
echo 'Stats preparation installed. Timer remains disabled; gateway integration requires separate approval.'
