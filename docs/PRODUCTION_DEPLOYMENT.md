# Production Deployment Guide

## Overview

This guide covers production deployment for **Transfer2Read** to the domain **transfer2read.app** (purchased on Namecheap).

**Production Domain:** `transfer2read.app`
**Production URLs:**
- Frontend: `https://transfer2read.app`
- Backend API: `https://transfer2read.app/api`

This is a Docker Compose-based application with FastAPI backend, Next.js frontend, Celery workers, and Redis.

---

## Current Architecture (Local Docker Compose)

**Services:**
- **Frontend**: Next.js 15 on port 3000
- **Backend API**: FastAPI on port 8000
- **Worker**: Celery worker for async AI processing
- **Beat**: Celery Beat scheduler for periodic tasks (monthly usage reset)
- **Redis**: Message broker and cache on port 6379
- **Supabase**: External managed service (PostgreSQL + Storage + Auth)

**Current Deployment:** All services run on a single host via Docker Compose with Supabase as an external dependency.

---

## Deployment Options

This guide provides multiple deployment approaches. Choose based on your infrastructure:

| Option | Best For | Pros | Cons |
|--------|----------|------|------|
| **Tailscale Funnel** | Local Mac/PC as server | No router config, automatic HTTPS, no dynamic IP issues, free | Mac must stay on |
| **Nginx + Let's Encrypt** | VPS/Cloud server | Industry standard, full control | Manual cert renewal, firewall setup |
| **Traefik** | Docker-native environments | Automatic cert renewal, service discovery | Learning curve |
| **Cloud Load Balancer** | AWS/GCP/Azure production | Managed service, DDoS protection | Higher cost |

**Recommended for Transfer2Read:**
- **Local Mac Server**: Use **Option 1 (Tailscale Funnel)** ⭐
- **VPS/Cloud Server**: Use **Option 2 (Nginx + Let's Encrypt)**

---

## Option 1: Tailscale Funnel (⭐ Recommended for Local Mac)

**Best for:** Running Transfer2Read on your local Mac as a production server.

### Architecture

```
Internet → Tailscale Funnel (HTTPS:443) → Local Mac → Docker Services
```

**Benefits:**
- ✅ No router configuration or port forwarding needed
- ✅ Automatic HTTPS with managed certificates
- ✅ No dynamic IP issues (Tailscale handles IP changes)
- ✅ More secure (home IP not exposed publicly)
- ✅ Easy DNS management with CNAME
- ✅ Free for personal use
- ✅ No Nginx or reverse proxy needed

### Prerequisites

- Tailscale account (free): https://tailscale.com
- Docker and Docker Compose installed
- Namecheap account access

### Step 1: Install Tailscale

```bash
# Install Tailscale via Homebrew
brew install tailscale

# Or download from: https://tailscale.com/download/mac

# Start Tailscale and authenticate
sudo tailscale up

# Enable Tailscale Funnel (public HTTPS access)
tailscale funnel 443 on

# Get your Tailscale hostname
tailscale status
```

You'll receive a hostname like: `your-macbook-name.tail-xxxxx.ts.net`

### Step 2: Configure Namecheap DNS

Update DNS to point your domain to Tailscale hostname using **CNAME records**:

1. **Log in to Namecheap:**
   - Go to https://www.namecheap.com/myaccount/login/
   - Navigate to **Domain List** → **transfer2read.app** → **Manage**
   - Click **Advanced DNS** tab

2. **Add CNAME records:**

   | Type  | Host | Value                                | TTL       |
   |-------|------|--------------------------------------|-----------|
   | CNAME | www  | `your-macbook-name.tail-xxxxx.ts.net` | Automatic |

3. **Configure root domain redirect:**

   Since some DNS providers don't allow CNAME on root domain (@), use URL redirect:

   | Type         | Host | Value                          | TTL |
   |--------------|------|--------------------------------|-----|
   | URL Redirect | @    | `https://www.transfer2read.app` | -   |

   Or if Namecheap supports ALIAS/ANAME records:

   | Type  | Host | Value                                | TTL       |
   |-------|------|--------------------------------------|-----------|
   | CNAME | @    | `your-macbook-name.tail-xxxxx.ts.net` | Automatic |

4. **Verify DNS propagation:**
   ```bash
   dig +short www.transfer2read.app
   # Should show: your-macbook-name.tail-xxxxx.ts.net
   ```

### Step 3: Configure Tailscale Funnel Routing

Tailscale Funnel routes external HTTPS traffic to your Docker services.

**Option A: Command-line configuration (Quick)**

```bash
# Expose frontend on HTTPS (port 443 → 3000)
tailscale funnel --bg --https=443 http://localhost:3000

# Note: Backend routing handled by Next.js proxy (see Step 4)
```

**Option B: Configuration file (Advanced)**

Create `~/.config/tailscale/funnel.json`:

```json
{
  "TCP": {
    "443": {
      "HTTPS": true
    }
  },
  "Web": {
    "${TS_CERT_DOMAIN}:443": {
      "Handlers": {
        "/": {
          "Proxy": "http://127.0.0.1:3000"
        },
        "/api/": {
          "Proxy": "http://127.0.0.1:8000"
        },
        "/docs": {
          "Proxy": "http://127.0.0.1:8000/docs"
        },
        "/redoc": {
          "Proxy": "http://127.0.0.1:8000/redoc"
        }
      }
    }
  }
}
```

Then enable:
```bash
tailscale funnel --config ~/.config/tailscale/funnel.json
```

### Step 4: Update Environment Variables

Edit `.env` file:

```env
# ====================
# CORS Configuration
# ====================
CORS_ORIGINS=https://transfer2read.app,https://www.transfer2read.app

# ====================
# Frontend Configuration
# ====================
# Backend API URL
NEXT_PUBLIC_BACKEND_URL=https://transfer2read.app/api

# Supabase (keep your existing values)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# ====================
# Backend Configuration
# ====================
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-key

# AI API Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Redis
REDIS_URL=redis://redis:6379/0
```

### Step 5: Update Next.js API Proxy (if needed)

If using Next.js to proxy API requests, update `frontend/next.config.ts`:

```typescript
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend-api:8000/api/:path*',
      },
    ];
  },
};
```

### Step 6: Start Docker Services

```bash
cd /Users/dominhxuan/Desktop/Transfer2Read

# Start all services
docker-compose up -d

# Verify all containers running
docker-compose ps

# Check logs
docker-compose logs -f
```

### Step 7: Verify Deployment

```bash
# Test Tailscale hostname directly
curl https://your-macbook-name.tail-xxxxx.ts.net

# Test custom domain (after DNS propagates)
curl https://www.transfer2read.app
curl https://www.transfer2read.app/api/health

# Check Tailscale Funnel status
tailscale funnel status
```

### Tailscale Deployment Checklist

- [ ] Install Tailscale: `brew install tailscale`
- [ ] Authenticate: `sudo tailscale up`
- [ ] Get hostname: `tailscale status`
- [ ] Enable Funnel: `tailscale funnel 443 on`
- [ ] Configure Funnel routing (command-line or config file)
- [ ] Update Namecheap DNS with CNAME records
- [ ] Update `.env` with production domains
- [ ] Start Docker services: `docker-compose up -d`
- [ ] Wait for DNS propagation (5-60 minutes)
- [ ] Test deployment: `curl https://www.transfer2read.app`
- [ ] Update Supabase OAuth callbacks to `https://www.transfer2read.app`

### Important Notes for Tailscale

1. **Mac must stay on**: Your Mac must remain powered on and connected to internet
2. **Automatic cert renewal**: Tailscale handles SSL certificate renewal automatically
3. **Free for personal use**: Tailscale Funnel is free for personal projects
4. **Better privacy**: Your home IP address is not exposed publicly
5. **No ISP restrictions**: Works even if ISP blocks port 80/443
6. **Easy updates**: Restart services with `docker-compose restart` - no SSL reconfiguration needed

### Troubleshooting Tailscale

**Funnel not working:**
```bash
# Check Tailscale status
tailscale status

# Check Funnel configuration
tailscale funnel status

# Check Docker logs
docker-compose logs -f

# Test direct access to services
curl http://localhost:3000
curl http://localhost:8000/api/health
```

**DNS not resolving:**
```bash
# Verify CNAME record
dig +short www.transfer2read.app

# Clear DNS cache
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

**502 Bad Gateway:**
- Ensure Docker services are running: `docker-compose ps`
- Check service logs: `docker-compose logs backend-api`
- Verify Tailscale routing: `tailscale funnel status`

---

## Option 2: Nginx Reverse Proxy (Recommended for VPS/Cloud)

**Architecture:**
```
Internet → Nginx (HTTPS:443) → Docker Services (HTTP:3000, HTTP:8000)
```

**Steps:**

1. **Add Nginx service to docker-compose.yml:**
   ```yaml
   nginx:
     image: nginx:alpine
     container_name: transfer2read-nginx
     restart: unless-stopped
     ports:
       - "80:80"
       - "443:443"
     volumes:
       - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
       - ./nginx/ssl:/etc/nginx/ssl:ro
     depends_on:
       - frontend
       - backend-api
   ```

2. **Create nginx.conf with SSL configuration:**
   ```nginx
   server {
       listen 80;
       server_name transfer2read.app www.transfer2read.app;
       return 301 https://transfer2read.app$request_uri;
   }

   server {
       listen 443 ssl http2;
       server_name transfer2read.app www.transfer2read.app;

       ssl_certificate /etc/nginx/ssl/fullchain.pem;
       ssl_certificate_key /etc/nginx/ssl/privkey.pem;
       ssl_protocols TLSv1.2 TLSv1.3;
       ssl_ciphers HIGH:!aNULL:!MD5;

       # Frontend (Next.js)
       location / {
           proxy_pass http://frontend:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }

       # Backend API
       location /api/ {
           proxy_pass http://backend-api:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Obtain SSL certificates:**
   - **Let's Encrypt (Free, automated):**
     ```bash
     # Install certbot
     sudo apt-get install certbot

     # Stop any running web services on ports 80/443
     docker-compose down

     # Generate certificates for transfer2read.app
     sudo certbot certonly --standalone \
       -d transfer2read.app \
       -d www.transfer2read.app \
       --email your-email@example.com \
       --agree-tos

     # Certificates will be in /etc/letsencrypt/live/transfer2read.app/
     # Copy to ./nginx/ssl/ directory
     sudo mkdir -p ./nginx/ssl
     sudo cp /etc/letsencrypt/live/transfer2read.app/fullchain.pem ./nginx/ssl/
     sudo cp /etc/letsencrypt/live/transfer2read.app/privkey.pem ./nginx/ssl/
     sudo chmod 644 ./nginx/ssl/fullchain.pem
     sudo chmod 600 ./nginx/ssl/privkey.pem
     ```

   - **Manual certificates** (for development/testing):
     ```bash
     openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
       -keyout nginx/ssl/privkey.pem \
       -out nginx/ssl/fullchain.pem
     ```

4. **Update environment variables:**
   ```env
   # .env
   CORS_ORIGINS=https://transfer2read.app,https://www.transfer2read.app
   NEXT_PUBLIC_BACKEND_URL=https://transfer2read.app
   ```

5. **Update Strict-Transport-Security header:**
   - Already implemented in `backend/app/main.py:32` (SecurityHeadersMiddleware)
   - Forces HTTPS for 1 year after first visit

5. **Start services with Nginx:**
   ```bash
   docker-compose up -d
   ```

6. **Verify HTTPS access:**
   ```bash
   curl https://transfer2read.app
   curl https://transfer2read.app/api/health
   ```

**Pros:**
- Industry-standard approach
- Centralized SSL termination
- Easy certificate management with Let's Encrypt
- Built-in rate limiting and security features

**Cons:**
- Additional service to manage
- Manual certificate renewal every 90 days (can be automated with cron)

---

### Option 2: Traefik Reverse Proxy (Docker-native, automatic SSL)

**Architecture:**
```
Internet → Traefik (HTTPS:443) → Docker Services
```

**Steps:**

1. **Add Traefik service to docker-compose.yml:**
   ```yaml
   traefik:
     image: traefik:v2.10
     container_name: transfer2read-traefik
     restart: unless-stopped
     command:
       - "--api.insecure=false"
       - "--providers.docker=true"
       - "--entrypoints.web.address=:80"
       - "--entrypoints.websecure.address=:443"
       - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
       - "--certificatesresolvers.letsencrypt.acme.email=your@email.com"
       - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
     ports:
       - "80:80"
       - "443:443"
     volumes:
       - /var/run/docker.sock:/var/run/docker.sock:ro
       - traefik_letsencrypt:/letsencrypt

   frontend:
     labels:
       - "traefik.enable=true"
       - "traefik.http.routers.frontend.rule=Host(`transfer2read.app`) || Host(`www.transfer2read.app`)"
       - "traefik.http.routers.frontend.entrypoints=websecure"
       - "traefik.http.routers.frontend.tls.certresolver=letsencrypt"

   backend-api:
     labels:
       - "traefik.enable=true"
       - "traefik.http.routers.api.rule=(Host(`transfer2read.app`) || Host(`www.transfer2read.app`)) && PathPrefix(`/api`)"
       - "traefik.http.routers.api.entrypoints=websecure"
       - "traefik.http.routers.api.tls.certresolver=letsencrypt"

   volumes:
     traefik_letsencrypt:
   ```

**Pros:**
- Automatic Let's Encrypt certificate management
- Docker-native configuration (labels in docker-compose.yml)
- Automatic service discovery
- Zero-downtime deployments

**Cons:**
- Learning curve for Traefik-specific configuration
- Requires Docker socket access (security consideration)

---

### Option 3: Cloud Provider Load Balancer (AWS/GCP/Azure)

**Architecture:**
```
Internet → ALB/Cloud Load Balancer (HTTPS:443) → EC2/VM (HTTP:3000, HTTP:8000)
```

**Steps:**

1. **AWS Application Load Balancer (ALB):**
   - Create ALB with HTTPS listener (port 443)
   - Attach ACM (AWS Certificate Manager) SSL certificate
   - Create target groups for frontend (port 3000) and backend (port 8000)
   - Configure path-based routing:
     - `/api/*` → Backend target group
     - `/*` → Frontend target group
   - Enable HTTP → HTTPS redirect (port 80 → 443)

2. **Google Cloud Load Balancer:**
   - Create Global HTTPS Load Balancer
   - Upload SSL certificate or use Google-managed certificate
   - Create backend services for frontend and backend
   - Configure URL map for path-based routing

3. **Update environment variables:**
   ```env
   CORS_ORIGINS=https://transfer2read.app,https://www.transfer2read.app
   NEXT_PUBLIC_BACKEND_URL=https://transfer2read.app
   ```

**Pros:**
- Managed service (no maintenance)
- Automatic SSL certificate renewal (cloud-managed certs)
- Built-in DDoS protection and WAF
- Health checks and auto-scaling

**Cons:**
- Additional cost (load balancer + data transfer)
- Vendor lock-in
- More complex setup

---

## Security Checklist for HTTPS Deployment

- [ ] SSL certificates obtained and configured
- [ ] HTTP → HTTPS redirect enabled
- [ ] HSTS header enabled (already in `backend/app/main.py:32`)
- [ ] CORS origins updated to HTTPS domains (`.env` → `CORS_ORIGINS`)
- [ ] Frontend API URL updated to HTTPS (`.env` → `NEXT_PUBLIC_BACKEND_URL`)
- [ ] Supabase callbacks updated to HTTPS (in Supabase dashboard)
- [ ] TLS 1.2+ enforced (disable TLS 1.0, 1.1)
- [ ] Strong cipher suites configured
- [ ] SSL certificate auto-renewal configured (Let's Encrypt)

---

## VPS/Cloud Server DNS Configuration (Option 2 Only)

**Note:** Skip this section if using **Option 1 (Tailscale)**. This section is only for VPS/cloud deployments.

Before deploying with Nginx + Let's Encrypt, configure DNS to point your domain to your server.

### Prerequisites

1. **Server IP address**: Your VPS/cloud server public IP (e.g., `203.0.113.45`)
2. **Namecheap account**: Access to manage `transfer2read.app` domain

### DNS Setup Steps

1. **Log in to Namecheap:**
   - Go to https://www.namecheap.com/myaccount/login/
   - Navigate to **Domain List** → **transfer2read.app** → **Manage**
   - Click **Advanced DNS** tab

2. **Configure A Records:**

   | Type  | Host | Value              | TTL       |
   |-------|------|-------------------|-----------|
   | A     | @    | `YOUR_SERVER_IP`  | Automatic |
   | A     | www  | `YOUR_SERVER_IP`  | Automatic |

   **Example:**
   ```
   Type: A Record
   Host: @
   Value: 203.0.113.45
   TTL: Automatic

   Type: A Record
   Host: www
   Value: 203.0.113.45
   TTL: Automatic
   ```

3. **Verify DNS propagation:**
   ```bash
   # Check if domain resolves to your server IP
   dig +short transfer2read.app
   dig +short www.transfer2read.app

   # Alternative: Use online tool
   # https://dnschecker.org/#A/transfer2read.app
   ```

   **Note:** DNS propagation can take 5-30 minutes.

4. **Firewall configuration:**
   ```bash
   # Ensure ports 80 and 443 are open on your server
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw status
   ```

---

## Recommended Approach for Transfer2Read

**Current Infrastructure:**
- **Domain:** `transfer2read.app` (Namecheap)
- **Server:** Local Mac (user's choice)
- **Deployment:** Docker Compose

**Recommended Setup:**
- Use **Option 1 (Tailscale Funnel)** ⭐ for local Mac deployment
- Simple, secure, automatic HTTPS with no router configuration
- Free for personal use

**Quick Start Checklist (Tailscale):**
1. ✅ Domain purchased: `transfer2read.app`
2. ⬜ Install Tailscale: `brew install tailscale && sudo tailscale up`
3. ⬜ Enable Funnel: `tailscale funnel 443 on`
4. ⬜ Configure Namecheap DNS with CNAME (see Option 1)
5. ⬜ Update .env with production URLs
6. ⬜ Start Docker services: `docker-compose up -d`
7. ⬜ Verify HTTPS access: `https://www.transfer2read.app`

**Alternative for VPS/Cloud:**
- Use **Option 2 (Nginx + Let's Encrypt)** if deploying to VPS
- Industry-standard approach with full control

---

## Next Steps

### For Tailscale Deployment (Recommended for Local Mac)

1. **Install Tailscale:**
   ```bash
   brew install tailscale
   sudo tailscale up
   ```

2. **Enable Tailscale Funnel:**
   ```bash
   tailscale funnel 443 on
   tailscale status
   ```

3. **Configure Namecheap DNS** with CNAME (see Option 1 above)

4. **Update `.env` with production URLs:**
   ```env
   CORS_ORIGINS=https://transfer2read.app,https://www.transfer2read.app
   NEXT_PUBLIC_BACKEND_URL=https://transfer2read.app/api
   ```

5. **Start Docker services:**
   ```bash
   cd /Users/dominhxuan/Desktop/Transfer2Read
   docker-compose up -d
   ```

6. **Configure Tailscale Funnel routing:**
   ```bash
   tailscale funnel --bg --https=443 http://localhost:3000
   ```

7. **Verify deployment:**
   ```bash
   curl https://www.transfer2read.app
   curl https://www.transfer2read.app/api/health
   ```

8. **Update Supabase OAuth callbacks** to `https://www.transfer2read.app`

### For VPS/Cloud Deployment (Option 2)

1. **Configure DNS in Namecheap** (see "VPS/Cloud Server DNS Configuration")
2. Wait for DNS propagation (5-30 minutes)
3. Choose deployment option (Nginx recommended)
4. Follow steps for chosen option
5. Update `.env` with production URLs
6. Restart services: `docker-compose down && docker-compose up -d`
7. Verify HTTPS access: `https://transfer2read.app`
8. Test SSL configuration: https://www.ssllabs.com/ssltest/analyze.html?d=transfer2read.app
9. Update Supabase OAuth callbacks to use `https://transfer2read.app`

---

## Related Files

- **CORS Configuration**: `backend/app/main.py:41-52`
- **Security Headers**: `backend/app/main.py:20-38`
- **Environment Template**: `.env.example:48-54`
- **Docker Compose**: `docker-compose.yml`

---

**Document Version:** 2.0
**Story Reference:** 7.1 - Production Environment Verification (AC#10)
**Last Updated:** 2026-01-08
**Deployment Method:** Tailscale Funnel (Local Mac) + Nginx (VPS/Cloud alternative)
