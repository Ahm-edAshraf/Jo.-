# 🎵 Discord Music Bot Hosting Guide

A comprehensive guide to hosting your Discord music bot and Lavalink server on free or low-cost platforms.

---

## 📊 Quick Comparison

| Platform | Free Tier | RAM | Always On | Credit Card | Best For |
|----------|-----------|-----|-----------|-------------|----------|
| **Railway** | $5/month credit | 512MB | ✅ Yes | ❌ No | Current setup, limited budget |
| **Fly.io** | 3 VMs free | 256MB each | ✅ Yes | ⚠️ Optional | Best Railway alternative |
| **Render** | 750 hrs/month | 512MB | ⚠️ Spins down | ❌ No | Simple deploys |
| **Koyeb** | 1 service free | 512MB | ✅ Yes | ❌ No | Easy migration |
| **Oracle Cloud** | 2 VMs forever | 1GB each ARM | ✅ Yes | ⚠️ Required | Best performance, truly free |
| **Replit** | Limited | 512MB | ❌ No | ❌ No | Testing only |

---

## 🚂 Railway (Current Setup)

Your bot is currently on Railway. Here's how to optimize it:

### Optimization Tips

1. **Procfile Updated**: We changed `web:` to `worker:` - this tells Railway it's a background process, not a web server.

2. **Environment Variables** (set in Railway dashboard):
   ```
   DISCORD_TOKEN=your_token
   GUILD_ID=your_guild_id (for instant command sync)
   LAVALINK_HOST=your_lavalink_host
   LAVALINK_PORT=2333
   LAVALINK_PASSWORD=your_password
   LAVALINK_SSL=false
   FORCE_SYNC=true (only on first deploy, then remove)
   ```

3. **Cost Estimation**:
   - Idle bot: ~$0.50-1.00/month
   - Active usage: ~$2-3/month
   - With 10s update interval + idle disconnect: savings of ~30-40%

### When $5 Runs Out

Railway gives $5 free credit. When depleted, you'll need to add payment or migrate.

---

## 🪰 Fly.io (Recommended Alternative)

**Best Railway replacement** - generous free tier, no credit card required initially.

### Free Tier
- 3 shared-cpu-1x VMs (256MB RAM each)
- 160GB outbound data transfer
- Up to 3GB persistent storage

### Setup Instructions

1. **Install Fly CLI**:
   ```bash
   # Windows (PowerShell)
   pwsh -Command "iwr https://fly.io/install.ps1 -useb | iex"
   
   # Or via npm
   npm install -g flyctl
   ```

2. **Login/Signup**:
   ```bash
   fly auth signup   # or fly auth login
   ```

3. **Create `fly.toml`** in your bot folder:
   ```toml
   app = "your-music-bot"
   primary_region = "sin"  # Singapore, or use "iad" (Virginia)
   
   [build]
     builder = "paketobuildpacks/builder:base"
   
   [env]
     LAVALINK_HOST = "your-lavalink-host"
     LAVALINK_PORT = "2333"
     LAVALINK_SSL = "false"
   
   [[services]]
     internal_port = 8080
     protocol = "tcp"
   
   [processes]
     worker = "python bot.py"
   ```

4. **Set Secrets**:
   ```bash
   fly secrets set DISCORD_TOKEN=your_token
   fly secrets set LAVALINK_PASSWORD=your_password
   fly secrets set GUILD_ID=your_guild_id
   ```

5. **Deploy**:
   ```bash
   fly launch --no-deploy
   fly deploy
   ```

### Hosting Lavalink on Fly.io

You can run both bot + Lavalink on Fly.io:

1. **Create Lavalink app**:
   ```bash
   mkdir lavalink && cd lavalink
   ```

2. **Create `Dockerfile`**:
   ```dockerfile
   FROM openjdk:17-slim
   WORKDIR /app
   RUN apt-get update && apt-get install -y wget
   RUN wget https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar
   COPY application.yml .
   EXPOSE 2333
   CMD ["java", "-jar", "Lavalink.jar"]
   ```

3. **Create `application.yml`**:
   ```yaml
   server:
     port: 2333
     address: 0.0.0.0
   lavalink:
     server:
       password: "your_secure_password"
       sources:
         youtube: true
         soundcloud: true
   ```

4. **Deploy Lavalink**:
   ```bash
   fly launch --name my-lavalink
   fly deploy
   ```

---

## 🎨 Render

**Simple GitHub-based deploys**, good free tier but spins down after 15 min inactivity.

### Free Tier
- 750 hours/month (enough for always-on)
- Auto-sleeps after 15 min (but Discord WebSocket keeps it alive)
- 512MB RAM

### Setup Instructions

1. Go to [render.com](https://render.com) and sign up
2. Click **"New +"** → **"Background Worker"**
3. Connect your GitHub repo
4. Configure:
   - **Name**: `music-bot`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. Add environment variables in the dashboard
6. Deploy!

### Limitations
- May have cold start delays
- Limited CPU burst

---

## 🥝 Koyeb

**Easy free tier**, similar to Railway but more generous.

### Free Tier
- 1 nano service (512MB RAM, 0.1 vCPU)
- Unlimited deployment
- No credit card required

### Setup Instructions

1. Go to [koyeb.com](https://koyeb.com) and sign up
2. Click **"Create App"** → **"GitHub"**
3. Select your repo
4. Configure:
   - **Builder**: `Buildpack`
   - **Run command**: `python bot.py`
   - **Instance type**: `Free (nano)`
5. Add environment variables
6. Deploy!

### Koyeb `Procfile`:
```
worker: python bot.py
```

---

## ☁️ Oracle Cloud (Best Free VPS)

**Truly free forever** - best option if you want full control and can handle Linux setup.

### Always Free Tier
- 2 AMD VMs (1GB RAM, 1/8 OCPU each) - or -
- 4 ARM VMs (24GB RAM total, 4 OCPUs total)
- 200GB block storage
- 10TB/month outbound data

### Setup Instructions

1. **Sign up** at [cloud.oracle.com](https://cloud.oracle.com) (credit card required but never charged)

2. **Create a VM**:
   - Go to Compute → Instances → Create Instance
   - Choose **"Always Free Eligible"** shape
   - Select Ubuntu 22.04
   - Download SSH keys

3. **SSH into your VM**:
   ```bash
   ssh -i your-key.pem ubuntu@your-vm-ip
   ```

4. **Install dependencies**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3-pip git openjdk-17-jdk -y
   ```

5. **Clone your bot**:
   ```bash
   git clone https://github.com/your/repo.git bot
   cd bot
   pip3 install -r requirements.txt
   ```

6. **Create `.env` file**:
   ```bash
   nano .env
   # Add your environment variables
   ```

7. **Run with systemd** (auto-start on boot):
   ```bash
   sudo nano /etc/systemd/system/musicbot.service
   ```
   
   ```ini
   [Unit]
   Description=Discord Music Bot
   After=network.target
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/bot
   ExecStart=/usr/bin/python3 bot.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   ```bash
   sudo systemctl enable musicbot
   sudo systemctl start musicbot
   ```

### Running Lavalink on Oracle

On the same VM:

```bash
# Download Lavalink
mkdir ~/lavalink && cd ~/lavalink
wget https://github.com/lavalink-devs/Lavalink/releases/latest/download/Lavalink.jar

# Create application.yml (see Fly.io section above)
nano application.yml

# Create systemd service
sudo nano /etc/systemd/system/lavalink.service
```

```ini
[Unit]
Description=Lavalink Server
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/lavalink
ExecStart=/usr/bin/java -jar Lavalink.jar
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable lavalink
sudo systemctl start lavalink
```

---

## 💻 Replit (Not Recommended)

Replit has changed their free tier significantly. **Not recommended** for production bots.

### Issues
- Free tier no longer supports "always on"
- Constant restarts
- Limited resources
- Deployments cost money

### If You Must Use Replit
1. Create a new Python Repl
2. Upload your bot files
3. Add secrets in the Secrets tab
4. Use an external uptime service (UptimeRobot) to ping it

---

## 🎧 Free Lavalink Hosting Options

If you don't want to host Lavalink yourself:

### Public Lavalink Nodes

> ⚠️ **Warning**: Public nodes may have unstable uptime and you're trusting them with your bot's audio traffic.

Check these resources for free public nodes:
- [lavalink.darrennathanael.com](https://lavalink.darrennathanael.com/)
- [Lavalink Hosting Discord servers](https://discord.gg/lavalink)

### Recommended Public Nodes (as of 2026)

```env
# Example public node (check for current availability)
LAVALINK_HOST=lavalink.devamop.in
LAVALINK_PORT=443
LAVALINK_PASSWORD=DevamOP
LAVALINK_SSL=true
```

### Self-Hosted Options

| Service | How to Host Lavalink |
|---------|---------------------|
| Fly.io | See instructions above |
| Oracle Cloud | Same VM as bot, free forever |
| Railway | Separate service, uses your $5 credit faster |

---

## 📈 Resource Usage Optimization

### Our Optimizations

| Change | Savings |
|--------|---------|
| 10s now-playing interval (was 5s) | ~50% less API calls |
| Idle disconnect (5 min) | Saves CPU when not in use |
| Queue limit (200 tracks) | Prevents memory overflow |
| Worker Procfile | Proper process management |
| Graceful shutdown | Clean disconnects |

### Estimated Monthly Usage

| Platform | Bot Only | Bot + Lavalink |
|----------|----------|----------------|
| Railway ($5 credit) | 2-5 months | 1-2 months |
| Fly.io (free tier) | Unlimited | Unlimited |
| Render (free tier) | Unlimited | Need paid |
| Koyeb (free tier) | Unlimited | Need paid |
| Oracle Cloud | Unlimited | Unlimited |

---

## 🚀 Migration Checklist

When moving from Railway to another platform:

- [ ] Export environment variables from Railway dashboard
- [ ] Ensure `Procfile` says `worker: python bot.py`
- [ ] Set `FORCE_SYNC=true` on first deploy to sync commands
- [ ] Test in a development guild first (`GUILD_ID` set)
- [ ] After testing, remove `GUILD_ID` for global commands
- [ ] Remove `FORCE_SYNC` after commands are synced
- [ ] Monitor for first 24 hours

---

## 🆘 Troubleshooting

### Bot not responding to commands?
1. Check `FORCE_SYNC=true` is set
2. Wait up to 1 hour for global sync
3. Use `GUILD_ID` for instant testing

### Lavalink connection failed?
1. Verify host/port/password
2. Check if Lavalink is running
3. Try a public node as fallback

### Bot disconnecting randomly?
1. Check idle timeout settings
2. Ensure voice channel has users
3. Monitor host's resource limits

---

## 📞 Support

- **Discord.py**: [discord.gg/dpy](https://discord.gg/dpy)
- **Mafic**: [GitHub Issues](https://github.com/ooliver1/mafic/issues)
- **Lavalink**: [discord.gg/lavalink](https://discord.gg/lavalink)
