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

# Use /etc/cron.d/ drop-in files (Debian/Ubuntu best practice)
# Atomic, idempotent, no collision with user crontab, re-run safe
cat > /etc/cron.d/agents-health << EOF
# AI CoS agents health check — every minute
* * * * * root ${AGENTS_DIR}/cron/health_check.sh >> ${AGENTS_DIR}/logs/health.log 2>&1
EOF
chmod 644 /etc/cron.d/agents-health

echo "Installing postgres backup cron (daily 2am UTC)..."
mkdir -p /opt/backups/postgres
cat > /etc/cron.d/agents-backup << 'EOF'
# AI CoS postgres backup — daily at 2am UTC, 7-day retention
0 2 * * * root . /opt/agents/.env && pg_dump $DATABASE_URL 2>/dev/null | gzip > /opt/backups/postgres/aicos-$(date +\%Y\%m\%d).sql.gz && find /opt/backups/postgres/ -mtime +7 -delete
EOF
chmod 644 /etc/cron.d/agents-backup

echo "Done. Start services with: systemctl start sync-agent web-agent content-agent"
echo "Cron jobs installed:"
ls -la /etc/cron.d/agents-*
