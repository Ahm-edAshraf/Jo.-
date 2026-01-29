# Discord Music Bot – Step-by-Step Setup Guide

Follow these steps in order. You can run the bot **locally** first to test, then deploy to **Railway** when ready.

---

## Part 1: Discord Application and Bot

### Step 1.1 – Create a Discord application

1. Open **[Discord Developer Portal](https://discord.com/developers/applications)** and log in with your Discord account.
2. Click **"New Application"** (top right).
3. Enter a name (e.g. `My Music Bot`) and click **Create**.
4. You are now on the app’s **General Information** page. Note the **Application ID** (you’ll use it for the invite link later).

### Step 1.2 – Create the bot user

1. In the left sidebar, click **"Bot"**.
2. Click **"Add Bot"** and confirm.
3. Under **Token**, click **"Reset Token"** (or **"View Token"** if it’s the first time).
4. **Copy the token** and store it somewhere safe (e.g. a password manager). You will **never** share this or commit it to git.
5. Optional but recommended:
   - Turn **OFF** “Public Bot” if you don’t want it listed.
   - Turn **ON** “Message Content Intent” only if you plan to read message content later (not required for slash commands + voice).

### Step 1.3 – Invite the bot to your server

1. In the left sidebar, click **"OAuth2"** → **"URL Generator"**.
2. Under **SCOPES**, check:
   - **bot**
   - **applications.commands**
3. Under **BOT PERMISSIONS**, check at least:
   - **View Channels**
   - **Connect** (voice)
   - **Speak** (voice)
   - **Use Voice Activity** (optional, for voice state)
4. Copy the **Generated URL** at the bottom.
5. Open that URL in your browser, choose your server, and click **Authorize**. Complete the captcha if asked.
6. The bot will appear in your server’s member list (offline until you run it).

---

## Part 2: Lavalink (local development)

The bot needs a **Lavalink** server to play audio. You run it once on your machine for local testing.

### Step 2.1 – Install Java 17+

1. Check if Java is installed: open a terminal and run:
   - **Windows (PowerShell):** `java -version`
   - You need **Java 17 or newer** (e.g. `openjdk 17` or `openjdk 21`).
2. If Java is missing or too old:
   - **Windows:** Install [Eclipse Temurin 17](https://adoptium.net/) or [Oracle JDK 17](https://www.oracle.com/java/technologies/downloads/).
   - **macOS:** `brew install openjdk@17`
   - **Linux:** e.g. `sudo apt install openjdk-17-jre` (or your distro’s package).

### Step 2.2 – Download and configure Lavalink

1. Create a folder for Lavalink, e.g. `d:\lavalink` (or `~/lavalink` on Mac/Linux).
2. Download the **Lavalink JAR** from:  
   **[Lavalink releases](https://github.com/lavalink-devs/lavalink/releases)**  
   Get the latest **Lavalink.jar** (e.g. `Lavalink-4.0.x.jar`).
3. In the same folder, create a file named **`application.yml`** with this content (you can change the password):

```yaml
server:
  port: 2333
  address: 0.0.0.0

lavalink:
  server:
    password: "youshallnotpass"
    sources:
      youtube: true
      soundcloud: true
```

4. Save the file. Your Lavalink folder should contain:
   - `Lavalink-4.0.x.jar` (or similar)
   - `application.yml`

### Step 2.3 – Run Lavalink

1. Open a terminal in the Lavalink folder (e.g. `d:\lavalink`).
2. Run (replace the JAR name with yours):

   **Windows (PowerShell):**
   ```powershell
   java -jar Lavalink-4.0.6.jar
   ```

   **macOS/Linux:**
   ```bash
   java -jar Lavalink-4.0.6.jar
   ```

3. Wait until you see something like **"Lavalink is ready to accept connections"**.
4. Leave this terminal open; Lavalink must keep running while you use the bot locally.
5. Defaults we’ll use:
   - **Host:** `127.0.0.1`
   - **Port:** `2333`
   - **Password:** `youshallnotpass` (same as in `application.yml`).

---

## Part 3: Bot environment and run (local)

### Step 3.1 – Prepare the bot folder

1. Open a terminal and go to the bot project:
   ```powershell
   cd d:\botmusic
   ```

2. (Recommended) Create a virtual environment so only this project’s dependencies are used:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   On macOS/Linux: `python3 -m venv venv` then `source venv/bin/activate`.

3. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
   If you previously had **py-cord** installed (and Mafic errors about “Multiple compatible libraries”), run:
   ```powershell
   pip uninstall py-cord -y
   ```
   Then install again: `pip install -r requirements.txt`.

### Step 3.2 – Create `.env` and set variables

1. In `d:\botmusic`, copy the example env file:
   - **Windows:** `copy .env.example .env`
   - **macOS/Linux:** `cp .env.example .env`

2. Open **`.env`** in an editor and set:

```env
DISCORD_TOKEN=your_bot_token_here
LAVALINK_HOST=127.0.0.1
LAVALINK_PORT=2333
LAVALINK_PASSWORD=youshallnotpass
LAVALINK_SSL=false
USE_YTDLP_FALLBACK=false
```

3. Replace **`your_bot_token_here`** with the bot token you copied in **Step 1.2**.
4. Save the file. **Do not** commit `.env` to git (it should be in `.gitignore`).

### Step 3.3 – Run the bot

1. Make sure **Lavalink is still running** in the other terminal (Part 2).
2. In the bot terminal (with venv active and `d:\botmusic` as the folder), run:
   ```powershell
   python bot.py
   ```
3. You should see something like:
   ```
   Logged in as YourBotName#1234 (ID: 123456789...)
   Slash commands synced.
   ```
4. In Discord, the bot should show as **Online**. Slash commands may take up to a minute to appear.

### Step 3.4 – Test in Discord

1. Join a **voice channel** in the server where you invited the bot.
2. In a text channel, type **`/music`** and you should see subcommands (play, pause, queue, etc.).
3. Run **`/music play`** and enter a search (e.g. `never gonna give you up`) or a YouTube URL.
4. The bot should join your voice channel and start playing. Try **`/music pause`**, **`/music resume`**, **`/music queue`**, **`/music volume 50`**, **`/music leave`**, etc.

If anything fails (e.g. “Could not join voice”, “Search failed”), check:
- Lavalink is running and shows “ready to accept connections”.
- `.env` has the correct `DISCORD_TOKEN`, `LAVALINK_HOST`, `LAVALINK_PORT`, `LAVALINK_PASSWORD`.
- You are in a voice channel when using `/music play`.

---

## Part 4: Deploy to Railway (production)

You’ll have **two services** on Railway: one for the **bot** and one for **Lavalink**. The bot connects to Lavalink over Railway’s private network.

### Step 4.1 – Push the bot code to GitHub

1. Create a new repository on **GitHub** (e.g. `my-music-bot`). Do **not** initialize with a README if your project already has one.
2. In `d:\botmusic`, initialize git if needed and add the remote:
   ```powershell
   git init
   git add .
   git commit -m "Initial music bot"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/my-music-bot.git
   git push -u origin main
   ```
3. Ensure **`.env`** is **not** committed (add `.env` to `.gitignore` if it isn’t already).

### Step 4.2 – Create a Railway project and add the Lavalink service

1. Go to **[railway.app](https://railway.app)** and log in (e.g. with GitHub).
2. Click **"New Project"**.
3. Choose **"Deploy from GitHub repo"** and connect your GitHub account if asked.
4. First we add **Lavalink** (so we can copy its internal URL for the bot):
   - Click **"+ New"** → **"Empty Service"** (or **"Database"** if you don’t see Empty Service; we just need a new service).
   - Rename this service to **"Lavalink"** (click the name).
   - In the Lavalink service, click **"Settings"** (or the gear). We will use a **template** or a **Dockerfile** for Lavalink. Railway has a Lavalink template:
     - Alternatively: **"+ New"** → **"Deploy a template"** and search for **"Lavalink"**. Deploy it; that becomes your Lavalink service.
   - If you use the **template**, it usually sets `LAVALINK_SERVER_PASSWORD`. Set it to something you choose (e.g. `youshallnotpass`) in the **Variables** tab.
   - If you use an **Empty Service** and deploy Lavalink yourself, you’ll need to add a **Dockerfile** or use **Nixpacks** with a Lavalink build. Easiest is to use Railway’s **Lavalink template** from the template gallery.
   - After deploy, open the **"Settings"** or **"Connect"** tab and find the **private network hostname** (e.g. `lavalink-production-xxxx.up.railway.app` or an internal host like `lavalink.railway.internal`). Also note the **port** (often **2333**). Railway may expose it via a public URL; for the bot we prefer the **internal** host/port if available (documentation: [Railway private networking](https://docs.railway.app/reference/private-networking)).

### Step 4.3 – Add the bot service and connect the repo

1. In the same Railway project, click **"+ New"** → **"GitHub Repo"** (or **"Empty Service"** then connect repo).
2. Select the **bot repository** (e.g. `my-music-bot`). Railway will create a new service and try to build it.
3. Rename this service to **"Bot"** (or "Music Bot").

### Step 4.4 – Set bot environment variables

1. Open the **Bot** service.
2. Go to the **"Variables"** tab.
3. Add:

| Name                 | Value                                                                 |
|----------------------|-----------------------------------------------------------------------|
| `DISCORD_TOKEN`      | Your bot token from Step 1.2                                         |
| `LAVALINK_HOST`      | Lavalink’s **internal** hostname (e.g. `lavalink.railway.internal` or the host shown in Lavalink service) |
| `LAVALINK_PORT`      | Lavalink port (e.g. `2333`)                                          |
| `LAVALINK_PASSWORD`  | Same password as Lavalink (e.g. `youshallnotpass`)                   |
| `LAVALINK_SSL`       | `false` (or `true` if your Lavalink service uses WSS/HTTPS)          |

4. Save. Railway will redeploy the bot when variables change.

### Step 4.5 – Set start command for the bot

1. In the **Bot** service, open **"Settings"**.
2. Find **"Start Command"** (or "Build & Deploy" → Start Command).
3. Set it to: **`python bot.py`**
4. If you use a **Procfile**, Railway may pick it up automatically (`web: python bot.py`). If not, the explicit start command ensures the bot runs.

### Step 4.6 – Deploy and check logs

1. Trigger a deploy (e.g. push a commit, or **"Deploy"** in the Bot service).
2. Open **"Deployments"** → latest deployment → **"View Logs"**.
3. You should see:
   ```
   Logged in as YourBotName#1234 (ID: ...)
   Slash commands synced.
   ```
4. If you see connection errors to Lavalink, check:
   - Lavalink service is running and healthy.
   - `LAVALINK_HOST` is the **internal** hostname (not the public URL unless that’s what Lavalink listens on).
   - `LAVALINK_PORT` and `LAVALINK_PASSWORD` match the Lavalink service.

5. In Discord, the bot should be online. Join a voice channel and use **`/music play`** to test.

---

## Part 5: Quick reference

### Local run (summary)

1. Start Lavalink: `java -jar Lavalink-4.0.6.jar` (in Lavalink folder).
2. Copy `.env.example` → `.env`, set `DISCORD_TOKEN` and Lavalink vars.
3. `pip install -r requirements.txt` (and `pip uninstall py-cord` if needed).
4. `python bot.py`.

### Railway (summary)

1. Lavalink service: deploy from Railway’s Lavalink template (or your own Lavalink deploy). Set password; note internal host and port.
2. Bot service: deploy from your GitHub repo; start command `python bot.py`.
3. Bot variables: `DISCORD_TOKEN`, `LAVALINK_HOST`, `LAVALINK_PORT`, `LAVALINK_PASSWORD`, `LAVALINK_SSL`.

### Useful commands in Discord

- **`/music play <query>`** – Play by URL or search.
- **`/music pause`** / **`/music resume`** – Pause / resume.
- **`/music queue`** – Show queue.
- **`/music nowplaying`** – Current track and progress.
- **`/music volume 80`** – Set volume 0–100.
- **`/music loop track`** – Loop current track.
- **`/music leave`** – Disconnect.
- **`/filter bassboost`** / **`/filter nightcore`** / **`/filter reset`** – Audio filters.

If you tell me which step you’re on (e.g. “Part 2 Lavalink” or “Part 4 Railway”), I can give the exact commands and clicks for your OS and screen.
