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