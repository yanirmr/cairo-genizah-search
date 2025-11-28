# Deployment Guide for Cairo Genizah Search

## Quick Start: Deploy in 5 Minutes

### Option 1: Railway.app (Recommended - $5/month)

**Prerequisites:**
- GitHub account
- Railway account (sign up at railway.app)

**Steps:**

1. **Push to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

2. **Deploy on Railway:**
   - Go to [railway.app](https://railway.app)
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect Python and deploy!

3. **Wait for build** (5-10 minutes for index to build)

4. **Get your URL** from the Railway dashboard

**Environment Variables to Set:**
- `INDEX_PATH`: `index/`

**Cost:** $5/month (includes $5 free credit to start)

---

### Option 2: Render.com (Free or $7/month)

**Steps:**

1. **Push to GitHub** (same as above)

2. **Deploy on Render:**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect GitHub repository
   - Render will use the `render.yaml` file automatically

3. **Choose plan:**
   - **Free**: Good for testing (sleeps after 15 min inactivity)
   - **Starter ($7/month)**: Always on, 1GB RAM

4. **Wait for deployment** (10-15 minutes)

**Note:** The index will be built during first deployment (configured in render.yaml)

---

### Option 3: Hetzner Cloud VPS (€4.51/month - Cheapest)

**Best for:** Those comfortable with Linux

**Steps:**

1. **Create Server:**
   - Go to [hetzner.com/cloud](https://www.hetzner.com/cloud)
   - Create account
   - Create new project
   - Add server: Ubuntu 22.04, CX11 (€4.51/month)

2. **SSH into server:**
```bash
ssh root@your-server-ip
```

3. **Setup application:**
```bash
# Update system
apt update && apt upgrade -y

# Install dependencies
apt install python3-pip python3-venv git nginx -y

# Clone repository
git clone <your-repo-url>
cd cairo_genizah_search

# Setup Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-prod.txt

# Build index
python -m genizah_search.indexer --input GenizaTranscriptions.txt --output index/

# Install process manager
pip install gunicorn
```

4. **Create systemd service:**
```bash
sudo nano /etc/systemd/system/genizah.service
```

Add:
```ini
[Unit]
Description=Cairo Genizah Search
After=network.target

[Service]
User=root
WorkingDirectory=/root/cairo_genizah_search
Environment="PATH=/root/cairo_genizah_search/venv/bin"
ExecStart=/root/cairo_genizah_search/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 genizah_search.app:app

[Install]
WantedBy=multi-user.target
```

5. **Start service:**
```bash
sudo systemctl daemon-reload
sudo systemctl start genizah
sudo systemctl enable genizah
```

6. **Configure Nginx:**
```bash
sudo nano /etc/nginx/sites-available/genizah
```

Add:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # or your-server-ip

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/genizah /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

7. **Access your app** at http://your-server-ip

---

### Option 4: DigitalOcean App Platform ($6/month)

**Steps:**

1. **Push to GitHub**

2. **Deploy:**
   - Go to [digitalocean.com](https://www.digitalocean.com)
   - Click "Create" → "Apps"
   - Connect GitHub repository
   - Select "Basic" plan ($6/month)

3. **Configure:**
   - Build Command: `pip install -r requirements-prod.txt && python -m genizah_search.indexer --input GenizaTranscriptions.txt --output index/ --quiet`
   - Run Command: `gunicorn -w 4 -b 0.0.0.0:$PORT genizah_search.app:app --timeout 120`

---

## Cost Comparison

| Provider | Cost/Month | RAM | Storage | Best For |
|----------|-----------|-----|---------|----------|
| Railway | $5 | 8GB | 100GB | Easiest deployment |
| Render Free | $0 | 512MB | 100GB | Testing/demos |
| Render Starter | $7 | 1GB | 100GB | Production |
| Hetzner CX11 | €4.51 | 4GB | 40GB SSD | Best value |
| DigitalOcean | $6 | 512MB | Varies | Popular choice |
| Fly.io | ~$3-5 | 256MB+ | Varies | Global CDN |

---

## Pre-Deployment Checklist

- [ ] Git repository initialized
- [ ] All code committed
- [ ] Pushed to GitHub
- [ ] Index built locally (or will build on deploy)
- [ ] Environment variables configured
- [ ] Test locally with: `gunicorn -b 0.0.0.0:5000 genizah_search.app:app`

---

## Post-Deployment

### Test Your Deployment

1. **Home page**: `https://your-app-url.com/`
2. **Search**: Try searching for "שבת"
3. **Stats**: Visit `/stats` to see index statistics
4. **API**: Test `https://your-app-url.com/api/stats`

### Monitor

- Railway: Built-in logs and metrics
- Render: Logs tab in dashboard
- Hetzner: `sudo journalctl -u genizah -f`

### Update Your App

**Railway/Render:**
```bash
git add .
git commit -m "Update"
git push
# Auto-deploys!
```

**Hetzner VPS:**
```bash
ssh root@your-server-ip
cd cairo_genizah_search
git pull
sudo systemctl restart genizah
```

---

## Troubleshooting

### App won't start
- Check logs for errors
- Verify index was built: `ls -lh index/`
- Check environment variables

### Slow performance
- Increase worker count: `-w 4` → `-w 6`
- Upgrade plan for more RAM
- Add caching

### Out of memory
- Reduce worker count
- Upgrade to larger plan
- Optimize index (reduce stored fields)

---

## Need Help?

- Railway: [docs.railway.app](https://docs.railway.app)
- Render: [render.com/docs](https://render.com/docs)
- Hetzner: [community.hetzner.com](https://community.hetzner.com)
