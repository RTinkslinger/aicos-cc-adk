#!/bin/bash
# Install systemd units and cron jobs for the 3-agent system.
# Run on droplet: bash /opt/agents/systemd/install.sh
set -e

AGENTS_DIR="/opt/agents"
SYSTEMD_DIR="/etc/systemd/system"

echo "Installing systemd units..."
cp ${AGENTS_DIR}/systemd/sync-agent.service ${SYSTEMD_DIR}/
cp ${AGENTS_DIR}/systemd/web-agent.service ${SYSTEMD_DIR}/
cp ${AGENTS_DIR}/systemd/content-agent.service ${SYSTEMD_DIR}/

systemctl daemon-reload
systemctl enable sync-agent web-agent content-agent

echo "Installing health check cron (every minute)..."
chmod +x ${AGENTS_DIR}/cron/health_check.sh

# Remove old agent cron entries, add new
crontab -l 2>/dev/null | grep -v 'agents' | crontab - 2>/dev/null || true
(crontab -l 2>/dev/null; echo "# agents: health check every minute") | crontab -
(crontab -l 2>/dev/null; echo "* * * * * ${AGENTS_DIR}/cron/health_check.sh >> ${AGENTS_DIR}/logs/health.log 2>&1 # agents") | crontab -

echo "Installing postgres backup cron (daily 2am UTC)..."
mkdir -p /opt/backups/postgres
(crontab -l 2>/dev/null; echo "# agents: postgres backup daily") | crontab -
(crontab -l 2>/dev/null; echo "0 2 * * * pg_dump \$DATABASE_URL 2>/dev/null | gzip > /opt/backups/postgres/aicos-\$(date +\\%Y\\%m\\%d).sql.gz && find /opt/backups/postgres/ -mtime +7 -delete # agents") | crontab -

echo "Done. Start services with: systemctl start sync-agent web-agent content-agent"
echo "Cron jobs installed:"
crontab -l | grep agents
