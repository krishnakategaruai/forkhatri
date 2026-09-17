#!/usr/bin/env bash
# =============================================================================
# Prepare a fresh Oracle Cloud Ubuntu 24.04 (aarch64) VM for ForKhatri. Idempotent.
# Normally run by `deploy/scripts/deploy.sh --bootstrap`; by hand: sudo bash server-bootstrap.sh
#
#   - security updates now, and unattended security updates (reboot 21:30 UTC = 03:00 IST if needed)
#   - Docker Engine + compose/buildx plugins from Docker's apt repository, log rotation
#   - 4 GB swap file (image builds), low swappiness
#   - UFW: deny all inbound except SSH (Cloudflare Tunnel is outbound-only)
#   - SSH: keys only, no root login
#   - /opt/forkhatri layout, rclone for off-server backups
#   - cron: nightly backup 21:00 UTC (02:30 IST), heartbeat every 5 minutes
#   - if a release is already deployed, `docker compose up -d`
# =============================================================================
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "run with sudo" >&2; exit 1; }
OWNER="${SUDO_USER:-ubuntu}"
BASE=/opt/forkhatri
export DEBIAN_FRONTEND=noninteractive
step() { echo; echo "==> $*"; }

. /etc/os-release
[ "${VERSION_ID:-}" = "24.04" ] || echo "WARNING: tested on Ubuntu 24.04, found ${PRETTY_NAME:-unknown}"
[ "$(dpkg --print-architecture)" = arm64 ] || echo "WARNING: expected arm64 (Ampere A1), found $(dpkg --print-architecture)"

step "Packages and security updates"
apt-get update -q
apt-get -y -q -o Dpkg::Options::=--force-confold upgrade
apt-get install -y -q ca-certificates curl gnupg ufw unattended-upgrades rclone cron gzip tar

step "Unattended security updates"
cat > /etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF
cat > /etc/apt/apt.conf.d/52forkhatri-unattended <<'EOF'
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "21:30";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
EOF
systemctl enable --now unattended-upgrades >/dev/null

step "Docker Engine"
if ! command -v docker >/dev/null || ! docker compose version >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -q
  apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'EOF'
{
  "log-driver": "local",
  "log-opts": { "max-size": "10m", "max-file": "5" },
  "live-restore": true
}
EOF
systemctl enable docker >/dev/null
systemctl restart docker
usermod -aG docker "$OWNER"
docker version --format 'docker {{.Server.Version}}'; docker compose version

step "Swap"
if ! swapon --show | grep -q /swapfile; then
  [ -f /swapfile ] || { fallocate -l 4G /swapfile; chmod 600 /swapfile; mkswap /swapfile >/dev/null; }
  swapon /swapfile
  grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi
echo 'vm.swappiness=10' > /etc/sysctl.d/90-forkhatri.conf
sysctl -q -p /etc/sysctl.d/90-forkhatri.conf
free -h | sed -n '1,3p'

step "SSH: keys only"
cat > /etc/ssh/sshd_config.d/60-forkhatri.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
EOF
sshd -t && systemctl reload ssh

step "Firewall: SSH only"
ufw --force reset >/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw limit OpenSSH
ufw --force enable
ufw status verbose | sed -n '1,12p'
# Oracle's image also ships iptables rules that allow only SSH; UFW sits alongside them.
# Docker publishes no ports in this stack, so nothing bypasses the firewall.

step "Layout"
mkdir -p "$BASE"/{releases,shared,backups,logs}
chown -R "$OWNER:$OWNER" "$BASE"
chmod 700 "$BASE/shared" "$BASE/backups"

step "Cron: nightly backup and heartbeat"
cat > /etc/cron.d/forkhatri <<EOF
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
# 21:00 UTC = 02:30 IST
0 21 * * * $OWNER [ -x $BASE/current/deploy/scripts/backup.sh ] && $BASE/current/deploy/scripts/backup.sh >> $BASE/logs/backup.log 2>&1
*/5 * * * * $OWNER [ -x $BASE/current/deploy/scripts/heartbeat.sh ] && $BASE/current/deploy/scripts/heartbeat.sh >/dev/null 2>&1
EOF
chmod 644 /etc/cron.d/forkhatri
systemctl enable --now cron >/dev/null

if [ -x "$BASE/current/deploy/scripts/compose.sh" ]; then
  step "Starting the deployed release"
  sudo -u "$OWNER" sg docker -c "$BASE/current/deploy/scripts/compose.sh up -d"
else
  echo; echo "Server ready. No release yet: deploy.sh uploads one and runs docker compose up -d."
fi
