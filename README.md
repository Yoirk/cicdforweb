# cicdforweb
Build CI/CD and apply it for developing website

## Overview

This project implements a comprehensive **DevSecOps pipeline** for a containerized web application with:
- Automated security scanning (SAST with Trivy, DAST with OWASP ZAP)
- Software Bill of Materials (SBOM) generation
- Container hardening and image pinning
- Nginx security header configuration
- Automated deployment to VPS

---

## Architecture

### Tech Stack
- **Web Server:** Nginx (Alpine Linux)
- **Containerization:** Docker & Docker Compose
- **CI/CD:** GitHub Actions
- **Security Scanning:** Trivy (SAST), OWASP ZAP (DAST), Syft (SBOM)
- **Notifications:** Discord

### Project Structure
```
cicdforweb/
├── .github/workflows/
│   └── deploy.yml           # Main CI/CD pipeline
├── html/                    # Static web content
├── nginx/
│   └── default.conf         # Nginx configuration with security headers
├── certs/                   # SSL/TLS certificates (Let's Encrypt)
├── docker-compose.yml       # Container orchestration (hardened)
└── README.md
```

---

## Security Controls Implemented

### 1. **Container Security**
- **Image Pinning:** Nginx pinned to `nginx:1.26.3-alpine` (specific tag)
- **Non-root User:** Container runs as user `101` (nginx)
- **Read-only Filesystem:** Mounted volumes are read-only (`:ro`)
- **Temporary Filesystem:** In-memory tmpfs for `/var/cache/nginx`
- **Resource Isolation:** No unbounded resource limits (optional to add)

### 2. **SSL/TLS Certificates**
- **Certificate Provider:** Let's Encrypt (via Certbot)
- **Location on VPS:** `/etc/letsencrypt/live/wanderingtomes.site/`
- **Deployment Process:** Certificates automatically copied to `/root/my-app/certs/` during pipeline
- **Renewal:** Certbot auto-renewal configured (every 60 days)
- **Post-Renewal Hook:** Automatically syncs certificates and restarts nginx container

   **Manual certificate renewal:**
   ```bash
   # On VPS
   certbot renew
   # Post-renewal hook automatically copies certificates and restarts nginx
   ```

   **Initial certificate setup (if needed):**
   ```bash
   # On VPS
   apt install -y certbot
   docker compose down
   certbot certonly --standalone -d wanderingtomes.site -d www.wanderingtomes.site --email your-email@example.com --agree-tos
   ```

### 3. **Static Application Security (SAST)**
- **Trivy Filesystem Scan:** Scans for vulnerabilities in dependencies and code
- **Trivy Image Scan:** Scans base image for known CVEs
- **Severity Filter:** Only CRITICAL and HIGH severity issues
- **Exit on Failure:** Pipeline stops if critical vulnerabilities found
- **SBOM Generation:** CycloneDX SBOM for both filesystem and container image

### 3. **Web Application Security**
- **Content Security Policy (CSP):** Restrictive CSP without unsafe-inline/eval
- **TLS Hardening:**
  - Enforced TLS 1.2 and 1.3
  - Modern cipher suites (ECDHE-based)
  - OCSP stapling enabled
- **Security Headers:**
  - X-Frame-Options: SAMEORIGIN (clickjacking protection)
  - X-Content-Type-Options: nosniff (MIME sniffing protection)
  - Strict-Transport-Security: 1-year HSTS
  - Referrer-Policy: strict-origin-when-cross-origin (privacy)
  - Permissions-Policy: Blocks camera, microphone, geolocation, payment

### 4. **Dynamic Application Security (DAST)**
- **OWASP ZAP Baseline Scan:** Automated scanning of live application
- **Non-blocking:** Scan failures don't block deployment (advisory)
- **Report Artifacts:** Results stored in GitHub Actions artifacts

### 5. **Supply Chain Security**
- **Action Pinning:** All GitHub Actions pinned to specific versions (no @master)
- **SBOM Artifacts:** SBOMs uploaded as CI artifacts for audit trail
- **SARIF Reports:** Trivy results in SARIF format for GitHub Security tab

### 6. **Deployment Security**
- **Secrets Management:** VPS credentials stored in GitHub Secrets
- **SSH Deployment:** Automated remote deployment with SSH
- **Pipeline Ordering:** Security scan must pass before deploy

---

## Deployment

### Prerequisites
1. **VPS Setup:**
   - Docker and Docker Compose installed
   - SSH access with key-based authentication
   - Writable directory at `/root/my-app` (or update target in deploy.yml)

2. **SSL/TLS Certificates:**
   - Place Let's Encrypt certificates in `./certs/` directory
   - Expected paths:
     ```
     certs/
     └── live/wanderingtomes.site/
           ├── fullchain.pem
           └── privkey.pem
     ```

3. **GitHub Secrets Configuration:**
   Set these secrets in your GitHub repository (Settings → Secrets and variables → Actions):
   - `VPS_HOST`: Your VPS IP address or hostname
   - `VPS_USER`: SSH username (e.g., `root`)
   - `SSH_PRIVATE_KEY`: Private SSH key for VPS access
   - `DISCORD_WEBHOOK`: Discord webhook URL for notifications

### Local Development

**Build and run locally:**
```bash
docker compose build
docker compose up -d
```

**Access the application:**
- HTTP (redirects to HTTPS): http://localhost
- HTTPS: https://localhost (self-signed cert warning)

**View logs:**
```bash
docker compose logs -f web
```

**Stop containers:**
```bash
docker compose down
```

### CI/CD Pipeline Execution

The pipeline triggers on:
- Push to `main` branch
- Pull requests to `main` branch

**Pipeline Stages:**
1. **Security Scan** (~5-10 min)
   - Trivy FS scan
   - Trivy image scan
   - Syft SBOM generation
   - Upload results to GitHub Security tab and artifacts

2. **Deploy** (~2-3 min) — *Runs only if security scan passes*
   - Copy files to VPS via SCP
   - Execute remote docker compose commands
   - Restart containers

3. **DAST Scan** (~5-10 min) — *Runs only if deploy succeeds*
   - OWASP ZAP baseline scan against deployed URL
   - Generate scan report

4. **Notify** (~1 min) — *Always runs*
   - Send Discord notification with status summary
   - Includes links to detailed logs

**View pipeline results:**
- GitHub Actions: Settings → Actions → Workflows → DevSecOps Pipeline
- Security tab: Shows Trivy SARIF results and artifacts
- Discord notifications: Status report in configured channel

---

## Security Best Practices Applied

### OWASP DevSecOps
- Automated scanning in CI
- Secrets management via GitHub Secrets
- Supply chain controls (action pinning)
- Artifact attestation (SBOM generation)
- TODO: Implement signed commits and code review enforcement

### SLSA Framework
- Automated CI/CD pipeline
- TODO: SLSA L3+ requires OIDC and provenance attestations
- TODO: Image signing with cosign

### Container Hardening
- Non-root user
- Read-only filesystem
- Image pinning
- TODO: Network policies and resource limits

### Web Security
- TLS 1.2+ enforcement
- Restrictive CSP
- Security headers (HSTS, X-Frame-Options, etc.)
- TODO: Subresource Integrity (SRI) for external resources

---

## Monitoring & Auditing

### Artifact Retention
- SBOM artifacts: 90 days (configurable in GitHub Actions)
- Scan reports: Available in Security tab for 90 days
- Logs: 30 days (GitHub default)

### Discord Notifications
Pipeline status is posted to Discord after every run:
- Project name and branch
- Security scan result
- Deployment result
- DAST scan result
- Link to full run details

### Manual Audit
```bash
# View SBOMs locally
unzip sbom-artifacts.zip
jq . sbom-fs.cyclonedx.json
jq . sbom-image.cyclonedx.json
```

---

## Configuration Files

### docker-compose.yml
Defines the Nginx container with:
- Pinned image by tag
- Read-only volume mounts
- Non-root user (UID 101)
- Tmpfs for cache directory

### nginx/default.conf
Web server configuration with:
- HTTP-to-HTTPS redirect
- TLS protocol and cipher hardening
- OCSP stapling
- Restrictive CSP
- Security headers
- Cache policies

### .github/workflows/deploy.yml
CI/CD pipeline with four jobs:
- `security-scan`: Trivy + Syft
- `deploy`: SCP + SSH remote execution
- `dast-scan`: OWASP ZAP
- `notify`: Discord notification

---

## Known Limitations & Future Work

1. **SSH Key Management:**
   - Currently uses long-lived SSH private key in GitHub Secrets
   - Future: Migrate to GitHub OIDC + ephemeral tokens or SSH certificates

2. **Image Signature Verification:**
   - No image signing or verification (cosign)
   - Future: Sign images in CI, verify before deploy

3. **Centralized Logging:**
   - No centralized log collection or audit trail
   - Future: Send logs to ELK/Datadog/CloudWatch

4. **Certificate Management:**
   - Manual certificate renewal required
   - Future: Automate with Certbot + ACME in CI

5. **Policy Enforcement:**
   - No branch protection or required code reviews
   - Future: Enforce via GitHub branch rules

---

## Troubleshooting

### Pipeline Fails on Security Scan
Check the "Security Scan" job output:
```bash
# View Trivy results
# GitHub Actions UI → DevSecOps Pipeline → security-scan job
```

If vulnerabilities are found:
1. Review the SARIF file in GitHub Security tab
2. Check `sbom-*.cyclonedx.json` artifacts for component details
3. Update base image or dependencies
4. Re-run pipeline after fixes

### Deployment Fails
Check SSH credentials:
```bash
# Verify secrets are set
# Settings → Secrets and variables → Actions
# Ensure SSH_PRIVATE_KEY is properly formatted (no extra spaces)
```

Check VPS connectivity:
```bash
# Test from local machine
ssh -i path/to/key user@vps_host "cd /root/my-app && docker compose ps"
```

### DAST Scan Takes Too Long
Baseline scan timeout: 10-15 minutes
- Reduce with smaller scope in `.zap/rules.tsv`
- Or increase `action-baseline` timeout parameter

---

## License & Attribution

This project implements security controls from:
- **OWASP Top 10 & DevSecOps Guidelines**
- **SLSA Supply Chain Security Framework**
- **CIS Docker Benchmark**
- **NIST Cybersecurity Framework**

---

## Support

For issues or questions:
1. Check GitHub Issues
2. Review pipeline logs in GitHub Actions
3. Validate configuration files against schema

# Echoes in the Void

A containerized FastAPI + Nginx web application for sharing thoughts, secured with a comprehensive DevSecOps pipeline.

---

## Overview

**Zero-trust DevSecOps pipeline** with:
- Multi-stage SAST/DAST security scanning (Trivy, OWASP ZAP, Bandit, Ruff, Gixy)
- Container signing with Cosign and SLSA provenance
- SBOM generation and attestation
- Hardened containers with read-only filesystems
- Automated deployment with signature verification
- Weekly VPS security audits

---

## Architecture

### Tech Stack
- **Frontend:** Vanilla JS, Tailwind CSS, Anime.js
- **Backend:** FastAPI, SQLite with Litestream S3 replication
- **Web Server:** Nginx (Alpine) with TLS 1.2/1.3
- **CI/CD:** GitHub Actions with 7-stage security gates
- **Security:** Trivy, OWASP ZAP, Bandit, Ruff, Gixy, Docker Bench, testssl.sh
- **Supply Chain:** Cosign, SLSA provenance, SBOM attestation

### Project Structure
```
cicdforweb/
├── .github/
│   ├── dependabot.yml
│   └── workflows/
│       ├── deploy.yml                # Main DevSecOps pipeline
│       └── audit-vps-schedule.yml    # Weekly VPS audit
├── backend/
│   ├── Dockerfile                    # Multi-stage build
│   ├── main.py                       # FastAPI with JWT auth
│   ├── requirements.txt
│   └── litestream.yml                # S3 replication
├── certs/live/wanderingtomes.site/   # Let's Encrypt SSL
├── html/index.html                   # SPA frontend
├── nginx/default.conf                # Hardened config
├── docker-compose.yml
├── Dockerfile                        # Nginx image
└── .trivyignore
```

---

## API Reference

### Authentication
- `POST /register` - Create user (Argon2 hash)
- `POST /login` - JWT token (60min expiry)

### Thoughts
- `POST /thoughts` - Create with mood (auth required)
- `GET /thoughts/random` - Fetch 8 random grouped by title
- `GET /thoughts/mine` - Get created + saved (auth required)
- `GET /thoughts/search?q=` - Search by title/content
- `DELETE /thoughts/{id}` - Delete own (auth required)

### Resonances
- `POST /thoughts/{id}/resonate` - Toggle bookmark (auth required)
- `GET /thoughts/{id}/resonated` - Check saved status (auth required)

**Database:** SQLite with WAL at `/data/app.db`, replicated to S3 every 10s.

---

## Security Controls

### Container Hardening
- **Image Pinning:** SHA256 digests for Nginx, Python, Golang
- **Non-root Users:** UID 101 (Nginx), UID 1001 (Backend)
- **Read-only Filesystem:** All containers with `read_only: true`
- **Tmpfs Mounts:** `/tmp` and `/var/run` in-memory
- **Resource Limits:** 0.5 CPU, 128MB (web) / 200MB (backend)

### SSL/TLS
- **Provider:** Let's Encrypt via Certbot
- **Protocols:** TLS 1.2/1.3 only
- **Ciphers:** ECDHE-ECDSA/RSA + AES-GCM + ChaCha20-Poly1305
- **OCSP Stapling:** Enabled
- **HSTS:** 1 year with includeSubDomains

### Web Security
- **Rate Limiting:** 10 req/s per IP (burst 20)
- **CSP:** Restrictive with CDN whitelisting
- **Headers:** X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- **Method Restrictions:** Static routes limited to GET/HEAD

### SAST Pipeline
- **TruffleHog:** Secret scanning (verified only)
- **Trivy:** Filesystem + config (CRITICAL/HIGH)
- **Checkov:** IaC scanning
- **Ruff:** Python linting
- **Gixy:** Nginx config vulnerabilities
- **Bandit:** Python security (High severity)

### DAST Pipeline
**CI Environment:**
- OWASP ZAP baseline (10 ignored rules)
- Vegeta rate-limit test (50 req/s, <80% success)
- Schemathesis API fuzzing (10 examples/endpoint)

**Production:**
- OWASP ZAP baseline (non-blocking)
- testssl.sh TLS/SSL scan (HIGH only)

### Supply Chain
- **Cosign Signing:** Keyless with GitHub OIDC
- **SLSA Provenance:** Build attestation (Level 2+)
- **SBOM:** CycloneDX format, 90-day retention
- **Verification:** Strict OIDC before deploy
  - Identity: `https://github.com/{repo}/.github/workflows/deploy.yml@refs/heads/main`
  - Issuer: `https://token.actions.githubusercontent.com`

### Continuous Monitoring
- **Weekly Audits:** Lynis (OS), Rkhunter (rootkit), Docker Bench (CIS)
- **Quality Gate:** Lynis score must be ≥60
- **Discord Notifications:** Automated reports with warning counts

---

## CI/CD Pipeline

### 7-Stage Flow
1. **Security SAST** (5-10 min) - TruffleHog, Trivy, Checkov, Ruff, Gixy, Bandit
2. **Build & Export** (3-5 min) - Buildx, Dive efficiency, SBOM, Trivy image scan
3. **DAST CI** (5-10 min) - ZAP, Vegeta, Schemathesis on localhost
4. **Push, Sign & Attest** (2-3 min) - GHCR push, Cosign sign, SLSA provenance
5. **Deploy** (3-5 min) - SCP configs, verify signatures, `docker compose up`
6. **DAST Prod** (5-10 min) - ZAP + testssl.sh on live URL
7. **Notify** (always) - Discord status summary

### Triggers
- Push/PR to `main` branch
- Ignores: `audit-vps-schedule.yml`, `README.md`

---

## Quick Start

### Local Development
```bash
docker compose build
docker compose up -d
docker compose logs -f
```

**Access:**
- HTTP: `http://localhost` (redirects to HTTPS)
- HTTPS: `https://localhost` (self-signed cert)
- Backend: `http://backend:8000` (container network)

### GitHub Secrets
Set in **Settings → Secrets and variables → Actions:**

| Secret | Description |
|--------|-------------|
| `VPS_HOST` | VPS IP/hostname |
| `VPS_USER` | SSH username |
| `SSH_PRIVATE_KEY` | Private key (PEM) |
| `AWS_ACCESS_KEY_ID` | S3 access key |
| `AWS_SECRET_ACCESS_KEY` | S3 secret key |
| `DISCORD_WEBHOOK` | Notification URL |

### Environment Variables
In [`docker-compose.yml`](docker-compose.yml):
- `SECRET_KEY` - JWT signing key
- `AWS_ACCESS_KEY_ID` → `LITESTREAM_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY` → `LITESTREAM_SECRET_ACCESS_KEY`
- `AWS_REGION` - Default: `ap-southeast-1`

---

## Troubleshooting

### Pipeline Fails on Security Scan
```bash
# Check job logs in GitHub Actions → DevSecOps Pipeline → security-sast
# Download SBOM artifacts to inspect dependencies
# Add exceptions to .trivyignore with justification
```

### Deployment Signature Verification Fails
```bash
# On VPS, check Cosign installation
cosign version

# Verify image digest matches
docker inspect --format='{{index .RepoDigests 0}}' <image>

# Confirm CERT_IDENTITY in deploy script
# Must match: https://github.com/{REPO}/.github/workflows/deploy.yml@refs/heads/main
```

### Rate Limit Not Working
```bash
# Test with Vegeta
echo "GET http://localhost/" | vegeta attack -duration=5s -rate=50 | vegeta report

# Success rate should be <80% with rate=50
# Verify Nginx config
docker exec web_proxy cat /etc/nginx/conf.d/default.conf | grep limit_req_zone
```

### Container Startup Fails
```bash
# SSH to VPS
docker compose logs backend
docker compose config
ls -la /root/my-app/
```

---

## Backup & Recovery

### SQLite Replication
- **Source:** `/data/app.db`
- **S3 Bucket:** `wanderingtomes-db-backup/production.db`
- **Interval:** 10 seconds
- **Region:** `ap-southeast-1`

### Restore
```bash
docker compose down
docker run --rm -v sqlite_data:/data \
  $(docker inspect --format='{{.Config.Image}}' python_api) \
  litestream restore -o /data/app.db s3://wanderingtomes-db-backup/production.db
docker compose up -d
```

---

## Security Standards Applied

- **OWASP DevSecOps:** Automated SAST/DAST, secrets management, supply chain controls
- **SLSA Level 2+:** Build provenance, keyless signing, strict verification
- **CIS Docker Benchmark:** Non-root users, read-only FS, weekly audits
- **NIST CSF:** Identify (SBOM), Protect (hardening), Detect (scanning), Respond (notifications)

### Future Work
- GitHub OIDC for VPS access (replace SSH keys)
- Centralized logging (ELK/Datadog)
- Automated Certbot renewal in CI
- Branch protection + required code reviews
- Secrets rotation with Vault/AWS Secrets Manager
- Per-user rate limiting with Redis

---

## Support

1. Check [GitHub Issues](../../issues)
2. Review [pipeline logs](../../actions)
3. Validate configs against schema
4. Check Discord notifications