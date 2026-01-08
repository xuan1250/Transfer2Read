# Nginx Configuration for Transfer2Read

This directory contains the Nginx reverse proxy configuration for production deployment of Transfer2Read to `transfer2read.app`.

## Files

- `nginx.conf` - Main Nginx configuration with SSL/HTTPS setup
- `ssl/` - Directory for SSL certificates (created during setup)

## Setup Instructions

### 1. Prerequisites

- Domain DNS configured (see `docs/PRODUCTION_DEPLOYMENT.md`)
- Server with Docker and Docker Compose installed
- Ports 80 and 443 open in firewall

### 2. Generate SSL Certificates

```bash
# Stop services if running
docker-compose down

# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Generate certificates
sudo certbot certonly --standalone \
  -d transfer2read.app \
  -d www.transfer2read.app \
  --email your-email@example.com \
  --agree-tos

# Copy certificates to nginx/ssl directory
sudo mkdir -p ./nginx/ssl
sudo cp /etc/letsencrypt/live/transfer2read.app/fullchain.pem ./nginx/ssl/
sudo cp /etc/letsencrypt/live/transfer2read.app/privkey.pem ./nginx/ssl/
sudo chmod 644 ./nginx/ssl/fullchain.pem
sudo chmod 600 ./nginx/ssl/privkey.pem
```

### 3. Add Nginx to docker-compose.yml

Add this service to your `docker-compose.yml`:

```yaml
nginx:
  image: nginx:alpine
  container_name: transfer2read-nginx
  restart: unless-stopped
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    - ./nginx/ssl:/etc/nginx/ssl:ro
  depends_on:
    - frontend
    - backend-api
```

### 4. Update Environment Variables

Edit `.env` file:

```env
CORS_ORIGINS=https://transfer2read.app,https://www.transfer2read.app
NEXT_PUBLIC_BACKEND_URL=https://transfer2read.app
```

### 5. Start Services

```bash
docker-compose up -d
```

### 6. Verify Deployment

```bash
# Test HTTPS access
curl https://transfer2read.app
curl https://transfer2read.app/api/health

# Check Nginx logs
docker logs transfer2read-nginx

# Test SSL configuration
# Visit: https://www.ssllabs.com/ssltest/analyze.html?d=transfer2read.app
```

## Certificate Renewal

Let's Encrypt certificates expire every 90 days. Set up automatic renewal:

```bash
# Create renewal script
sudo tee /etc/cron.monthly/renew-transfer2read-ssl.sh > /dev/null <<'EOF'
#!/bin/bash
# Renew SSL certificates for transfer2read.app

# Stop Nginx to free port 80
cd /path/to/Transfer2Read
docker-compose stop nginx

# Renew certificates
certbot renew --standalone

# Copy new certificates
cp /etc/letsencrypt/live/transfer2read.app/fullchain.pem ./nginx/ssl/
cp /etc/letsencrypt/live/transfer2read.app/privkey.pem ./nginx/ssl/
chmod 644 ./nginx/ssl/fullchain.pem
chmod 600 ./nginx/ssl/privkey.pem

# Restart Nginx
docker-compose start nginx
EOF

# Make executable
sudo chmod +x /etc/cron.monthly/renew-transfer2read-ssl.sh
```

## Troubleshooting

### Port Conflicts

If port 80 or 443 is already in use:

```bash
# Check what's using the ports
sudo lsof -i :80
sudo lsof -i :443

# Stop conflicting services
sudo systemctl stop apache2  # or nginx
```

### SSL Certificate Errors

```bash
# Verify certificate files exist
ls -la ./nginx/ssl/

# Check certificate details
openssl x509 -in ./nginx/ssl/fullchain.pem -text -noout

# View Nginx error logs
docker logs transfer2read-nginx
```

### Connection Issues

```bash
# Test DNS resolution
dig +short transfer2read.app

# Test port connectivity
telnet transfer2read.app 443

# Check firewall rules
sudo ufw status
```

## Security Notes

- Certificate private key (`privkey.pem`) should have `600` permissions
- Never commit SSL certificates to git (already in `.gitignore`)
- Update certificates before they expire (90 days for Let's Encrypt)
- Monitor SSL Labs score: https://www.ssllabs.com/ssltest/

## Related Documentation

- Full deployment guide: `docs/PRODUCTION_DEPLOYMENT.md`
- Story 7.1: `docs/sprint-artifacts/7-1-production-environment-verification.md`
- Docker Compose configuration: `docker-compose.yml`
