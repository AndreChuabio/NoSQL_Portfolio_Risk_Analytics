# Environment Variables - Copy-Paste Guide

**Quick Reference:** Use this guide to set up your database connections.  
**For full setup:** See `TEAMMATE_SETUP.md` for complete onboarding.

---

## Required Environment Variables

You need 4 environment variables to connect to MongoDB Atlas and Redis Cloud:

```bash
export MONGODB_URI="mongodb+srv://username:password@clusterac1.od00ttk.mongodb.net/?retryWrites=true&w=majority"
export REDIS_HOST="redis-12345.c123.us-east-1-1.ec2.redns.redis-cloud.com"
export REDIS_PORT="12345"
export REDIS_PASSWORD="your_redis_password"
```

**Get these values from Andre** - they contain sensitive credentials.

---

## Setup Method 1: Use the Setup Script (Recommended)

```bash
cd /Users/andrechuabio/NoSQL_Project
source setup_env.sh
```

The script will:
1. Prompt you to paste each credential
2. Set them for your current terminal session
3. Optionally save them to `~/.zshrc` for persistence across sessions

**This is the easiest method - just copy-paste the values Andre gives you.**

---

## Setup Method 2: Manual Terminal Commands (Quick Test)

Copy-paste these commands with your actual values:

```bash
export MONGODB_URI="mongodb+srv://username:password@clusterac1.od00ttk.mongodb.net/?retryWrites=true&w=majority"
export REDIS_HOST="redis-12345.c123.us-east-1-1.ec2.redns.redis-cloud.com"
export REDIS_PORT="12345"
export REDIS_PASSWORD="your_redis_password"
```

**Note:** These only last for your current terminal session. Close the terminal and they're gone.

---

## Setup Method 3: Permanent Setup (Edit Shell Config)

To make credentials persist across terminal sessions:

```bash
# Open your shell config file
nano ~/.zshrc  # macOS default shell

# Add these lines at the end (paste your actual values):
export MONGODB_URI="mongodb+srv://username:password@clusterac1.od00ttk.mongodb.net/?retryWrites=true&w=majority"
export REDIS_HOST="redis-12345.c123.us-east-1-1.ec2.redns.redis-cloud.com"
export REDIS_PORT="12345"
export REDIS_PASSWORD="your_redis_password"

# Save and exit (Ctrl+O, Enter, Ctrl+X in nano)

# Reload your shell config
source ~/.zshrc
```

Now these variables will be available in every new terminal window.

---

## Verification Commands

After setting variables, verify they're configured correctly:

### Check Variables Are Set

```bash
echo "MONGODB_URI: ${MONGODB_URI:0:30}..."
echo "REDIS_HOST: $REDIS_HOST"
echo "REDIS_PORT: $REDIS_PORT"
echo "REDIS_PASSWORD: ${REDIS_PASSWORD:0:5}***"
```

Expected output:
```
MONGODB_URI: mongodb+srv://username:passw...
REDIS_HOST: redis-12345.c123.us-east-1-1.ec2.redns.redis-cloud.com
REDIS_PORT: 12345
REDIS_PASSWORD: aBcDe***
```

### Test MongoDB Connection

```bash
python -c "from config.mongodb_config import get_mongo_client; client = get_mongo_client(); print('MongoDB connected:', client.admin.command('ping'))"
```

Expected output:
```
MongoDB connected: {'ok': 1.0}
```

### Test Redis Connection

```bash
python src/ingestion/verify_redis.py
```

Expected output:
```
✓ Redis PING successful
✓ String write/read successful
✓ TTL set successfully
✓ JSON cache successful
✓ Hash operations successful
✓ Cleanup successful
Redis Verification: ALL TESTS PASSED
```

---

## Copy-Paste Template

Ask Andre to fill this out for you, then copy-paste into your terminal:

```bash
# MongoDB Atlas connection string
export MONGODB_URI="[ANDRE FILLS THIS IN]"

# Redis Cloud connection details
export REDIS_HOST="[ANDRE FILLS THIS IN]"
export REDIS_PORT="[ANDRE FILLS THIS IN]"
export REDIS_PASSWORD="[ANDRE FILLS THIS IN]"
```

---

## Troubleshooting

### Variables Not Persisting After Closing Terminal

**Problem:** Variables work in one terminal but not new ones  
**Solution:** Add them to `~/.zshrc` (see Method 3 above) and run `source ~/.zshrc`

### MongoDB Connection Refused

**Problem:** "ServerSelectionTimeoutError" or connection timeout  
**Solution:**
1. Check `MONGODB_URI` is set correctly: `echo $MONGODB_URI`
2. Verify IP is whitelisted in MongoDB Atlas (ask Andre to add `0.0.0.0/0` in Network Access)
3. Check internet connection

### Redis Connection Refused

**Problem:** "Connection refused" or "Authentication failed"  
**Solution:**
1. Verify variables: `echo $REDIS_HOST && echo $REDIS_PORT && echo $REDIS_PASSWORD`
2. Double-check values from Redis Cloud dashboard (ask Andre)
3. Check internet connection

### "MONGODB_URI not set" Error

**Problem:** Script says environment variable is missing  
**Solution:**
1. Run `source setup_env.sh` again, OR
2. Manually export the variables (see Method 2)
3. Verify with `echo $MONGODB_URI`

### Special Characters in Password

**Problem:** Password contains `@`, `#`, `:`, or other special characters  
**Solution:** URL-encode them in the MongoDB URI:
- `@` → `%40`
- `#` → `%23`
- `:` → `%3A`
- `/` → `%2F`

Example:
```bash
# Original password: MyP@ss#123
# Encoded in URI: MyP%40ss%23123
export MONGODB_URI="mongodb+srv://user:MyP%40ss%23123@cluster..."
```

---

## Security Best Practices

### DO:
- ✅ Store credentials in your local `~/.zshrc` file (not committed to Git)
- ✅ Use the `setup_env.sh` script which is already in `.gitignore`
- ✅ Keep credentials private - don't share in chat, screenshots, or commits

### DON'T:
- ❌ Commit credentials to GitHub
- ❌ Share credentials in public channels
- ❌ Hardcode credentials in Python files
- ❌ Store credentials in plain text files in the repo

The `.gitignore` already excludes:
- `.env` files
- `setup_env.sh` (if you customize it)
- Any file with credentials in the name

---

## For Windows Users

If you're on Windows, replace `~/.zshrc` with your shell's config file:

**PowerShell:**
```powershell
# Set for current session
$env:MONGODB_URI="mongodb+srv://..."
$env:REDIS_HOST="redis-12345..."
$env:REDIS_PORT="12345"
$env:REDIS_PASSWORD="your_password"

# Set permanently (requires admin)
[Environment]::SetEnvironmentVariable("MONGODB_URI", "mongodb+srv://...", "User")
```

**Git Bash (Windows):**
```bash
# Edit ~/.bashrc instead of ~/.zshrc
nano ~/.bashrc
# Add export commands, save, and run:
source ~/.bashrc
```

---

**Quick Links:**
- Full setup guide: `docs/TEAMMATE_SETUP.md`
- Project status: `docs/status/phase2_status.md`
- Get credentials from: Andre Chuabio (andre102599@gmail.com)
