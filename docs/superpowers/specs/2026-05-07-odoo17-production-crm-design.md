# Odoo 17 Community Edition Production Installation Design
**Date:** 2026-05-07  
**Status:** Design Phase  
**Objective:** Deploy Odoo 17 Community Edition on ClawZ840 as a production CRM system to replace Go High Level (GHL)

---

## 1. Executive Summary

This design specifies a production-grade installation of Odoo 17 Community Edition on Ubuntu 24.04 LTS, configured as a CRM and sales automation platform to replace Go High Level. The installation uses a source-based approach with PostgreSQL database backend, Nginx reverse proxy with self-signed SSL, and systemd service management. All Odoo apps/modules will be installed; the admin user will configure pipelines, teams, and CRM workflows through the Odoo UI.

---

## 2. Architecture Overview

### 2.1 System Components

```
┌─────────────────────────────────────────┐
│     HTTPS Client (https://100.124.71.12)│
└──────────────────┬──────────────────────┘
                   │ HTTPS (443)
┌──────────────────▼──────────────────────┐
│   Nginx (Reverse Proxy)                 │
│   - SSL Termination (self-signed)       │
│   - Port 443 → localhost:8069           │
└──────────────────┬──────────────────────┘
                   │ HTTP (localhost:8069)
┌──────────────────▼──────────────────────┐
│   Odoo 17 (Source Install)              │
│   - Python 3.12 runtime                 │
│   - Systemd service (odoo.service)      │
│   - Running as 'odoo' system user       │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│   PostgreSQL 16                         │
│   - Database: odoo17_production         │
│   - Owner: odoo (system user)           │
└─────────────────────────────────────────┘
```

### 2.2 Server Environment
- **Host:** ClawZ840 (Linux)
- **OS:** Ubuntu 24.04.4 LTS
- **Python:** 3.12.3 (pre-installed)
- **User Access:** SSH via Tailscale (scott@100.124.71.12)

---

## 3. Installation Components

### 3.1 System Dependencies
- **PostgreSQL 16** — database backend (required)
- **Git** — to clone Odoo source repository
- **Python development libraries** — build tools for Python packages
- **Node.js & npm** — for less/sass CSS compilation
- **wkhtmltopdf** — PDF rendering for reports
- **libpq-dev, libxml2-dev** — PostgreSQL and XML bindings
- **Nginx** — reverse proxy and SSL termination

### 3.2 Odoo 17 Community Source
- Clone from official repository: `https://github.com/odoo/odoo.git`
- Branch: `17.0`
- Installation path: `/opt/odoo/odoo-17-production`

### 3.3 Python Packages
- Install via pip from Odoo's `requirements.txt`
- Core dependencies: psycopg2, werkzeug, Babel, jinja2, etc.
- Virtual environment: `/opt/odoo/.venv/` (isolated Python environment)

---

## 4. Database Configuration

### 4.1 PostgreSQL Setup
- **Version:** PostgreSQL 16 (latest stable)
- **System user:** `postgres` (manages the database)
- **Odoo database:** `odoo17_production`
- **Database owner:** `odoo` (system user, created during setup)
- **Authentication:** Local socket authentication (no password required for local connections)

### 4.2 Access Control
- Only the `odoo` system user can access the database
- No remote database access (secure by default)

### 4.3 Backup Strategy
- Daily backups stored in `/var/backups/odoo/`
- Backup format: PostgreSQL dump (pg_dump)
- Retention: 7 days local backups (external storage TBD)

---

## 5. Odoo Application Setup

### 5.1 System User & Permissions
- **System user:** `odoo` (UID/GID auto-assigned)
- **Home directory:** `/opt/odoo/`
- **Permissions:** No shell access, minimal privileges
- **File ownership:** All Odoo files owned by `odoo:odoo`

### 5.2 Odoo Configuration
- **Configuration file:** `/etc/odoo/odoo.conf`
- **Log file:** `/var/log/odoo/odoo.log`
- **Port:** 8069 (internal, not exposed directly)
- **Workers:** 4 (configurable based on load testing; start with 4)
- **Database:** `odoo17_production`
- **Admin user:** Created during initial setup (email: user-specified)

### 5.3 Modules & Apps
All Odoo Community Edition modules will be installed:
- **CRM** — contacts, leads, opportunities, sales pipelines (GHL replacement)
- **Sales** — quotations, orders, invoicing
- **Accounting** — general ledger, accounts payable/receivable
- **Marketing Automation** — email campaigns, lead scoring
- **Calendar** — scheduling and meetings
- **Email Marketing** — bulk emails, templates
- **HR** — employee management (optional, available)
- **All other community apps** — available in the app store UI

Configuration of pipelines, teams, and workflows will be done through the Odoo UI after deployment.

---

## 6. SSL/TLS & Network Configuration

### 6.1 Self-Signed SSL Certificate
- **Certificate location:** `/etc/nginx/ssl/odoo.crt` and `/etc/nginx/ssl/odoo.key`
- **Generation:** Using openssl with 365-day validity
- **Subject CN:** `100.124.71.12` (server IP)
- **Note:** Browser will show "untrusted certificate" warning; user accepts and continues

### 6.2 Nginx Reverse Proxy
- **Listen:** 0.0.0.0:443 (HTTPS, all interfaces)
- **SSL termination:** Nginx decrypts HTTPS, forwards plain HTTP to Odoo
- **Redirect:** HTTP (port 80) → HTTPS (port 443)
- **Proxy to:** http://localhost:8069

### 6.3 Access
- **URL:** https://100.124.71.12
- **Access method:** Internal network via Tailscale, or direct SSH tunnel if needed

---

## 7. Service Management

### 7.1 Systemd Service
- **Service file:** `/etc/systemd/system/odoo.service`
- **Start/stop:** `systemctl start|stop|restart odoo`
- **Status:** `systemctl status odoo`
- **Enable on boot:** `systemctl enable odoo`
- **Logs:** `journalctl -u odoo -f` (follow logs in real-time)
- **Auto-restart:** Enabled; if Odoo crashes, systemd restarts it automatically

### 7.2 Logging
- **Odoo logs:** `/var/log/odoo/odoo.log`
- **System logs:** `/var/log/syslog` (also logged to systemd journal)
- **Log rotation:** Configured with logrotate (prevents disk fill)

---

## 8. Security & Access Control

### 8.1 Initial Access
- First login: Admin user created during setup
- Credentials: Email address + generated password (provided to user)
- **IMPORTANT:** Change password immediately after first login

### 8.2 User Management
- All user management (teams, permissions, roles) done through Odoo UI
- Default: Admin user only; add additional users as needed
- Role-based access control configured per module

### 8.3 Network Security
- **Odoo service:** Listens on localhost:8069 only (not exposed to network)
- **Public interface:** Only Nginx on port 443 is publicly accessible
- **SSH access:** Via Tailscale VPN (100.124.71.12)
- **Firewall:** Ubuntu firewall rules can be configured as needed

### 8.4 Database Security
- **Local socket auth:** No password transmitted over network
- **User isolation:** Only `odoo` system user can connect to the database
- **No remote access:** Database not exposed to the network

---

## 9. Post-Installation Setup (UI Configuration)

### 9.1 Admin Configuration
After deployment, the admin user will:
1. Log in to https://100.124.71.12
2. Configure company details, currency, timezone
3. Set up CRM pipelines and stages (replacing GHL workflows)
4. Create sales teams and assign members
5. Configure email integration (optional)
6. Set up custom fields and workflows as needed

### 9.2 Data Import (Future)
- If migrating data from GHL: Use Odoo's import tools or custom scripts
- **Not included in this design** — to be planned separately

---

## 10. Monitoring & Maintenance

### 10.1 Operational Monitoring
- **Service health:** Check systemd status regularly
- **Log monitoring:** Review `/var/log/odoo/odoo.log` for errors
- **Database size:** Monitor with `du -sh /var/lib/postgresql/`
- **Disk space:** Ensure `/var` and `/opt` partitions have adequate free space

### 10.2 Backup & Recovery
- **Backup schedule:** Daily via cron job (7-day retention local)
- **Recovery:** Restore from backup using pg_restore
- **Testing:** Backups should be tested monthly

### 10.3 Updates & Patches
- **OS updates:** Apply Ubuntu security patches monthly
- **Odoo updates:** Plan for testing before applying to production
- **Python packages:** Review and test security updates

---

## 11. Future Enhancements (Out of Scope)

These are not part of the initial installation but can be added later:
- **Email integration:** Connect to SMTP/POP3 for auto-lead capture
- **API integrations:** Zapier, webhooks, custom integrations
- **Multi-company:** If needed for different business lines
- **Custom modules:** Build domain-specific features
- **CDN/caching:** For performance optimization
- **External backups:** S3, cloud storage for disaster recovery
- **Monitoring tools:** Prometheus, Grafana for advanced monitoring
- **Load balancing:** If scaling to multiple Odoo instances

---

## 12. Installation Timeline & Effort

- **System preparation:** 15 minutes (user/directory setup)
- **Dependencies & PostgreSQL:** 20 minutes
- **Odoo source & Python packages:** 15 minutes
- **Configuration (odoo.conf, systemd, Nginx):** 15 minutes
- **SSL certificate & Nginx setup:** 10 minutes
- **Testing & verification:** 10 minutes
- **Total estimated time:** ~90 minutes

---

## 13. Success Criteria

The installation is complete when:
- [ ] Nginx responds with HTTPS on port 443
- [ ] https://100.124.71.12 loads the Odoo login page (with SSL warning)
- [ ] Admin login works with credentials created during setup
- [ ] All CRM, Sales, and Marketing modules are visible in the app menu
- [ ] Odoo database is backed up daily
- [ ] Systemd service auto-restarts on failure
- [ ] Logs are clean (no critical errors in `/var/log/odoo/odoo.log`)

---

## 14. Rollback Plan

If installation fails:
1. Stop Odoo service: `systemctl stop odoo`
2. Remove Odoo directory: `rm -rf /opt/odoo/odoo-17-production`
3. Drop database: `dropdb odoo17_production`
4. Restore Nginx to original config: `systemctl stop nginx`
5. Investigate logs and retry

No data loss occurs if installation is abandoned before first use.

---

## 15. References & Links

- **Odoo 17 Documentation:** https://www.odoo.com/documentation/17.0/
- **PostgreSQL 16 Docs:** https://www.postgresql.org/docs/16/
- **Nginx Documentation:** https://nginx.org/en/docs/
- **Ubuntu 24.04 LTS:** https://wiki.ubuntu.com/Noble
