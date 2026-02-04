# 🚀 ECapps Production IaaS Infrastructure

A complete, production-grade Infrastructure-as-Code (IaaS) system for deploying and managing multiple web applications, static sites, and databases on a single VPS with Docker, GitHub Actions CI/CD, and automated schema migrations.

**Status**: ✅ Production Ready | **Version**: 2.0 | **Last Updated**: February 2026

---

## 📋 Quick Overview

This repository manages:
- ✅ **4 static web applications** deployed to Nginx
- ✅ **Automated database migrations** with JSON schemas
- ✅ **SSL/TLS certificates** via Let's Encrypt
- ✅ **Nginx proxy management** with admin dashboard
- ✅ **Docker container orchestration** and monitoring
- ✅ **GitHub Actions CI/CD** for fully automated deployments
- ✅ **Multi-environment** configuration management

**Key Numbers:**
- `apps.json` - Single configuration file for all apps
- `docker-compose.yml` - Full stack in one file
- 5 production environments deployed
- 0 manual deployment steps (fully automated)
- ~15 minutes per deployment end-to-end

---

## 🏗️ Infrastructure Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   GITHUB ACTIONS CI/CD                      │
│  (Automated: Plan → Build → Test → Deploy → Verify)        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   VPS (Linux Server)                        │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Docker & Docker Compose                 │  │
│  │                                                        │  │
│  │  ┌──────────────┐  ┌────────────┐  ┌────────────┐   │  │
│  │  │ Nginx Proxy  │  │ Portainer  │  │ MariaDB    │   │  │
│  │  │ Manager      │  │ Dashboard  │  │ 10.11      │   │  │
│  │  │              │  │            │  │            │   │  │
│  │  │ :80, :81,    │  │ :9000      │  │ :3306      │   │  │
│  │  │ :443         │  │            │  │            │   │  │
│  │  └──────────────┘  └────────────┘  └────────────┘   │  │
│  │         ↓                                             │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │     Static Sites (Nginx)                     │   │  │
│  │  │                                              │   │  │
│  │  │ • ecapps.in                                  │   │  │
│  │  │ • friendselectricals.store                   │   │  │
│  │  │ • devsuite.ecapps.in                         │   │  │
│  │  │ • madhumanish.studio                         │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                                                        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  Shared Network: hosting_net (bridge)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
ecapps-production-iaas/
│
├── 📄 README.md                          # This file
├── 📄 README_DOCS.md                     # Documentation index
├── 📄 apps.json                          # ⭐ APPLICATION CONFIGURATION
├── 📄 docker-compose.yml                 # ⭐ INFRASTRUCTURE DEFINITION
├── 📄 versions.env                       # Version management
├── 📄 Dockerfile                         # Custom Docker images
│
├── configs/                              # Configuration files
│   ├── mysql/
│   │   └── custom.cnf                   # MariaDB settings
│   └── php/
│       └── php.ini                      # PHP settings
│
├── data/                                 # Runtime data (git-ignored)
│   ├── npm-data/                        # Nginx Proxy Manager
│   ├── npm-letsencrypt/                 # SSL certificates
│   ├── portainer-data/                  # Portainer dashboard
│   └── schemas/                         # Database schemas
│
├── .github/
│   ├── scripts/
│   │   ├── configure_npm.py             # Nginx proxy auto-config
│   │   └── schema_migrator.py            # Database migration engine
│   │
│   └── workflows/
│       ├── production_pipeline.yml       # ⭐ MAIN CI/CD PIPELINE
│       └── daily-backup.yml             # Backup automation
│
└── 📚 Documentation/
    ├── GETTING_STARTED.md               # 5-minute quickstart
    ├── SCHEMA_MIGRATION_GUIDE.md        # Database setup guide
    ├── IMPLEMENTATION_SUMMARY.md        # Technical deep-dive
    ├── JSON_SCHEMA_REFERENCE.md         # JSON schema format
    ├── TROUBLESHOOTING.md               # Problem solving
    ├── WHATS_NEW.md                     # System overview
    └── CHECKLIST.md                     # Implementation verification
```

### Key Files Explained

**⭐ `apps.json`** - Single source of truth for all applications
- Defines static sites, containers, and databases
- Specifies repositories, branches, build commands
- Auto-detected and deployed by the pipeline

**⭐ `docker-compose.yml`** - Complete infrastructure definition
- Nginx Proxy Manager (reverse proxy, SSL/TLS)
- Portainer (Docker management dashboard)
- MariaDB (database server)
- Shared network for inter-service communication

**⭐ `.github/workflows/production_pipeline.yml`** - Automated deployment
- Triggered on push to `production` branch
- 5-stage pipeline: Plan → Build → Test → Deploy → Verify
- Handles statics, containers, and database migrations

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- VPS with Linux (Ubuntu 20.04+ recommended)
- GitHub repository with workflow secrets configured
- SSH access to VPS configured

### 1️⃣ Clone Repository
```bash
git clone <repo-url>
cd ecapps-production-iaas
```

### 2️⃣ Configure Apps
Edit `apps.json` to add your applications:
```json
{
  "apps": [
    {
      "name": "your-app",
      "type": "static",
      "repo_url": "owner/repo",
      "branch": "main",
      "build_cmd": "npm install && npm run build",
      "output_dir": "dist",
      "domain": "your-app.com"
    }
  ]
}
```

### 3️⃣ Deploy to Production
Push to production branch:
```bash
git add apps.json
git commit -m "Add new application"
git push origin production
```

Watch the CI/CD pipeline execute automatically:
```
📥 Checkout → 🧮 Analyze → 🐳 Build → 🚀 Deploy → ✅ Verify
```

### 4️⃣ Access Services
- **Applications**: https://your-domain.com
- **Nginx Admin**: http://vps-ip:81 (default creds: admin@example.com / changeme)
- **Portainer**: http://vps-ip:9000 (Docker management)
- **Databases**: VPS port 3306 (with authentication)

---

## 📊 Supported Application Types

### Static Sites (`type: "static"`)
- **Framework Support**: Angular, React, Vue, Next.js, etc.
- **Build Process**: NPM, Webpack, Vite, etc.
- **Example**: 
  ```json
  {
    "name": "ecapps.in",
    "type": "static",
    "repo_url": "ecappmakers/ecapps",
    "branch": "main",
    "build_cmd": "npm install && npm run build",
    "output_dir": "dist/ecapps-single/browser",
    "domain": "ecapps.in"
  }
  ```

### Containers (`type: "container"`)
- **Support**: Any Docker-compatible application
- **Usage**: Backend APIs, Node.js services, Java apps
- **Example**:
  ```json
  {
    "name": "api-service",
    "type": "container",
    "repo_url": "owner/api-repo",
    "branch": "main",
    "docker_registry": "ghcr.io/owner",
    "image_name": "api-service"
  }
  ```

### Databases (`type: "database"`)
- **Support**: MariaDB 10.11
- **Automated Migrations**: JSON-based schema definitions
- **Example**:
  ```json
  {
    "name": "app-database",
    "type": "database",
    "repo_url": "owner/database-schema",
    "branch": "master"
  }
  ```

---

## 📚 Documentation Guide

### 🎯 Choose Your Path

**👤 I'm New Here**
→ Start with [GETTING_STARTED.md](GETTING_STARTED.md) (5 minutes)

**🔧 I Need Full Setup**
→ Read [SCHEMA_MIGRATION_GUIDE.md](SCHEMA_MIGRATION_GUIDE.md) (30 minutes)

**⚙️ I'm Technical**
→ Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) (1 hour)

**📋 I Need Examples**
→ See [JSON_SCHEMA_REFERENCE.md](JSON_SCHEMA_REFERENCE.md)

**🆘 Something's Wrong**
→ Visit [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**📇 Full Index**
→ Navigate [README_DOCS.md](README_DOCS.md)

---

## 🔄 CI/CD Pipeline Stages

### Stage 1️⃣: Plan & Detect
- Reads `apps.json`
- Detects application types (static, container, database)
- Creates build matrices for parallel execution
- Outputs: List of apps to build, deploy counts

### Stage 2️⃣: Build
**For Static Sites:**
- Clone repository from GitHub
- Run `build_cmd` (npm install, build, etc.)
- Create artifact with `output_dir` contents

**For Containers:**
- Clone repository
- Build Docker image
- Push to registry (Docker Hub, GitHub Container Registry)

**For Databases:**
- Clone schema repository
- Extract `db-config.json`
- Copy schema definitions

### Stage 3️⃣: Test
- Validate Docker images
- Test connectivity to VPS
- Verify application health checks
- Confirm SSL certificates

### Stage 4️⃣: Deploy
**To VPS:**
- SCP static artifacts to `/opt/ecapps-hosting/`
- Pull container images on VPS
- Update docker-compose configuration
- Sync database schemas to `/opt/ecapps-hosting/data/schemas/`

**Database Migrations:**
- Execute Python migration script
- Compare JSON schemas with current database
- Generate and apply SQL migrations
- Track changes in migration history

### Stage 5️⃣: Verify
- Confirm all services healthy
- Check domain DNS resolution
- Validate SSL certificates active
- Run smoke tests
- Report status

---

## 🗄️ Database Management

### Schema Setup
Databases use JSON-based schema definitions instead of SQL:

```json
{
  "tables": {
    "users": {
      "columns": {
        "id": { "type": "INT", "primary_key": true, "auto_increment": true },
        "username": { "type": "VARCHAR(255)", "nullable": false, "unique": true },
        "email": { "type": "VARCHAR(255)", "nullable": false },
        "created_at": { "type": "TIMESTAMP", "default": "CURRENT_TIMESTAMP" }
      }
    }
  }
}
```

### Automatic Migrations
The pipeline automatically:
1. Detects schema changes
2. Generates migration SQL
3. Compares with current database
4. Applies only necessary changes
5. Tracks migration history

### Connection Details
```bash
Host: <VPS-IP>
Port: 3306
Username: <configured-per-database>
Password: <GitHub-secret>
```

See [SCHEMA_MIGRATION_GUIDE.md](SCHEMA_MIGRATION_GUIDE.md) for full database setup.

---

## 🔐 Security Features

### Secret Management
- All passwords stored in GitHub Secrets
- Never committed to repository
- Injected at deployment time
- Per-database user accounts

### SSL/TLS Certificates
- Automatic via Let's Encrypt
- Managed by Nginx Proxy Manager
- Auto-renewal enabled
- Free certificates

### Network Isolation
- Docker internal network (`hosting_net`)
- Services only accessible via Nginx proxy
- Database port not exposed to public
- SSH key-based VPS access

### Access Control
- Nginx admin protected by credentials
- Portainer requires authentication
- GitHub Actions secrets protected
- SSH keys for VPS deployment

---

## 🔧 Configuration

### Version Management (`versions.env`)
Control component versions:
```env
JRE_VERSION=11
TOMCAT_MAJOR=10
TOMCAT_VERSION=10.1.18
PHP_APACHE_VERSION=8.2-apache
MARIADB_VERSION=10.11
```

Update versions, push to production, and infrastructure automatically upgrades.

### Application Settings
- **MySQL**: `configs/mysql/custom.cnf`
- **PHP**: `configs/php/php.ini`
- **Apps**: Individual settings in `apps.json`

### Environment Variables
Set in GitHub Secrets:
- `VPS_HOST` - VPS IP or hostname
- `VPS_USER` - SSH user (usually root)
- `VPS_SSH_KEY` - Private SSH key for VPS access
- `GH_USER` - GitHub username
- `GH_TOKEN` - GitHub personal access token
- `DB_PASS` - Default database password

---

## 📈 Monitoring & Management

### Portainer Dashboard
Access at `http://vps-ip:9000`
- View all containers
- Check resource usage
- View logs in real-time
- Manage volumes and networks

### Nginx Proxy Manager
Access at `http://vps-ip:81`
- Add new domains
- Configure SSL certificates
- View traffic statistics
- Manage proxy hosts

### Logs
Each service logs to Docker:
```bash
# View logs for service
docker logs <container-name>

# Stream logs (follow mode)
docker logs -f <container-name>

# View last 100 lines
docker logs --tail 100 <container-name>
```

### Health Checks
Services have built-in health checks:
```bash
# Check service health
docker ps --filter "name=nginx_proxy"

# View health status
docker inspect <container-name>
```

---

## 🚨 Troubleshooting

### Build Fails?
1. Check `apps.json` syntax: `jq . apps.json`
2. Verify repository URLs are accessible
3. Check build commands work locally first
4. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Deploy Fails?
1. Verify VPS is accessible: `ssh -i key.pem user@vps-ip`
2. Check disk space: `df -h`
3. View deploy logs in GitHub Actions
4. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Domain Not Accessible?
1. Verify DNS points to VPS IP
2. Check Nginx Proxy Manager configuration
3. Ensure SSL certificate is valid
4. Confirm firewall allows ports 80, 443

### Database Issues?
1. Verify database is running: `docker ps`
2. Check connection: `mysql -h <ip> -u <user> -p`
3. Review migration logs on VPS
4. Check `/opt/ecapps-hosting/migration_history.json`
5. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 📖 Advanced Topics

### Adding a New Application
1. Create new repository with your app
2. Add entry to `apps.json` with:
   - Name, type, repo_url, branch
   - Build command (for statics/containers)
   - Output directory (for statics)
   - Domain name
3. Push to `production` branch
4. Pipeline automatically builds and deploys

### Multiple Databases
Each database gets:
- Independent repository with JSON schemas
- Separate user account for security
- Automatic migration handling
- Dedicated configuration in `db-config.json`

See [SCHEMA_MIGRATION_GUIDE.md](SCHEMA_MIGRATION_GUIDE.md) section 5.

### Custom Docker Images
Create `Dockerfile` for custom base images used by applications:
```dockerfile
FROM php:8.2-apache
RUN apt-get update && apt-get install -y curl
```

### Backup & Recovery
Daily backups configured via `.github/workflows/daily-backup.yml`:
- Database dumps
- Application data
- Configuration files
- SSL certificates

---

## 📋 Current Deployed Applications

| App | Type | Domain | Repository | Status |
|-----|------|--------|------------|--------|
| ECapps | Static | ecapps.in | ecappmakers/ecapps | ✅ Live |
| Friends Electricals | Static | friendselectricals.store | ecappmakers/friends-electricals-home | ✅ Live |
| DevSuite | Static | devsuite.ecapps.in | ecappmakers/DevSuite | ✅ Live |
| Madhumanish Studio | Static | madhumanish.studio | MathumithaArumugam/madhumanishstudio | ✅ Live |
| Database Schema | Database | — | ecappmakers/database-schema | ✅ Active |

---

## 🛠️ Common Commands

### Local Testing
```bash
# Validate JSON
jq . apps.json

# Test with Docker Compose locally
docker-compose up -d

# View services
docker-compose ps

# View logs
docker-compose logs -f nginx_proxy

# Stop everything
docker-compose down
```

### VPS Management
```bash
# Connect to VPS
ssh -i /path/to/key.pem user@vps-ip

# Check services
docker ps
docker ps -a

# View application files
ls -la /opt/ecapps-hosting/

# Check database
mysql -h 127.0.0.1 -u root -p

# View migration history
cat /opt/ecapps-hosting/migration_history.json
```

### CI/CD Debugging
```bash
# Manually trigger pipeline
# (via GitHub UI: Actions → Workflow → "Run Workflow")

# View pipeline logs in GitHub
# Actions → production_pipeline → Latest Run → View Logs

# Check artifact downloads
# Workflow → Summary → Artifacts
```

---

## 🤝 Contributing

### Process
1. Create feature branch from main
2. Make changes to `apps.json` or configuration
3. Test locally: `docker-compose up -d`
4. Commit changes with clear message
5. Push to `production` for automatic deployment

### Before Deploying
- ✅ Validate `apps.json` with `jq`
- ✅ Test build commands locally
- ✅ Verify repository URLs are accessible
- ✅ Check SSL certificate requirements
- ✅ Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues

---

## 📞 Support & Help

### Documentation
- **Quick Start**: [GETTING_STARTED.md](GETTING_STARTED.md)
- **Full Guide**: [SCHEMA_MIGRATION_GUIDE.md](SCHEMA_MIGRATION_GUIDE.md)
- **Technical**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
- **Problems**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Issues
For issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) first
2. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md#debugging) debugging section
3. Check GitHub Issues in this repository
4. Contact infrastructure team

---

## 📝 License & Ownership

- **Repository**: ecapps-production-iaas
- **Owner**: EApp Makers
- **Status**: Active Production
- **Last Updated**: February 4, 2026

---

## 🎯 Quick Reference

| Need | Location | Time |
|------|----------|------|
| Start here | [GETTING_STARTED.md](GETTING_STARTED.md) | 5 min |
| Add app | Update `apps.json`, push to production | 2 min |
| Setup database | [SCHEMA_MIGRATION_GUIDE.md](SCHEMA_MIGRATION_GUIDE.md) section 3 | 15 min |
| Modify table | Edit JSON in schema repo, push | 5 min |
| Fix issue | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) | varies |
| View logs | GitHub Actions or Portainer | 2 min |
| Manage domains | Nginx Proxy Manager admin UI | 5 min |
| Check status | `docker ps` on VPS | 1 min |

---

## ✅ System Checklist

Before going live:
- [ ] VPS set up and SSH accessible
- [ ] GitHub Secrets configured
- [ ] `apps.json` validated with `jq`
- [ ] Docker Compose tested locally
- [ ] First deployment successful
- [ ] Applications accessible via domain
- [ ] SSL certificates active
- [ ] Backups running daily
- [ ] Monitoring in place
- [ ] Team trained on documentation

---

## 🚀 Getting Started Now

**First time here?** Start with 5-minute guide:
```bash
cd ecapps-production-iaas
cat GETTING_STARTED.md
```

**Ready to deploy?** Push to production:
```bash
git add .
git commit -m "Deployment: [description]"
git push origin production
```

**Need help?** See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) or read [README_DOCS.md](README_DOCS.md) for full index.

---

**System Status**: ✅ **Production Ready**  
**Last Deployment**: [Check GitHub Actions]  
**Next Steps**: Configure your first application in `apps.json` and deploy!
