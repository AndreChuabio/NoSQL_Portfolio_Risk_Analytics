#!/bin/bash
# Environment Setup Script for NoSQL Portfolio Risk Analytics
# Usage: source setup_env.sh (must use 'source' to set variables in current shell)

echo "=== NoSQL Portfolio Risk Analytics - Environment Setup ==="
echo ""

# MongoDB Atlas Configuration
echo "MongoDB Atlas Configuration:"
echo "----------------------------"
read -p "Enter your MongoDB URI (mongodb+srv://...): " MONGODB_URI_INPUT
export MONGODB_URI="$MONGODB_URI_INPUT"

echo ""

# Redis Cloud Configuration
echo "Redis Cloud Configuration:"
echo "--------------------------"
read -p "Enter Redis Host (redis-xxxxx.redns.redis-cloud.com): " REDIS_HOST_INPUT
read -p "Enter Redis Port (e.g., 12345): " REDIS_PORT_INPUT
read -s -p "Enter Redis Password (hidden): " REDIS_PASSWORD_INPUT
echo ""

export REDIS_HOST="$REDIS_HOST_INPUT"
export REDIS_PORT="$REDIS_PORT_INPUT"
export REDIS_PASSWORD="$REDIS_PASSWORD_INPUT"

echo ""
echo "=== Environment Variables Set ==="
echo "MONGODB_URI: ${MONGODB_URI:0:30}..."
echo "REDIS_HOST: $REDIS_HOST"
echo "REDIS_PORT: $REDIS_PORT"
echo "REDIS_PASSWORD: ${REDIS_PASSWORD:0:5}***"
echo ""

# Ask if user wants to persist to ~/.zshrc
read -p "Do you want to add these to ~/.zshrc for permanent setup? (y/n): " PERSIST

if [ "$PERSIST" = "y" ] || [ "$PERSIST" = "Y" ]; then
    # Backup existing .zshrc
    if [ -f ~/.zshrc ]; then
        cp ~/.zshrc ~/.zshrc.backup.$(date +%Y%m%d_%H%M%S)
        echo "Backed up existing .zshrc"
    fi
    
    # Remove old entries if they exist
    grep -v "MONGODB_URI=" ~/.zshrc > ~/.zshrc.tmp || true
    grep -v "REDIS_HOST=" ~/.zshrc.tmp > ~/.zshrc.tmp2 || true
    grep -v "REDIS_PORT=" ~/.zshrc.tmp2 > ~/.zshrc.tmp3 || true
    grep -v "REDIS_PASSWORD=" ~/.zshrc.tmp3 > ~/.zshrc.tmp4 || true
    mv ~/.zshrc.tmp4 ~/.zshrc
    rm -f ~/.zshrc.tmp ~/.zshrc.tmp2 ~/.zshrc.tmp3
    
    # Add new entries
    echo "" >> ~/.zshrc
    echo "# NoSQL Portfolio Risk Analytics - Database Credentials" >> ~/.zshrc
    echo "export MONGODB_URI=\"$MONGODB_URI\"" >> ~/.zshrc
    echo "export REDIS_HOST=\"$REDIS_HOST\"" >> ~/.zshrc
    echo "export REDIS_PORT=\"$REDIS_PORT\"" >> ~/.zshrc
    echo "export REDIS_PASSWORD=\"$REDIS_PASSWORD\"" >> ~/.zshrc
    
    echo "✓ Added to ~/.zshrc - variables will persist across terminal sessions"
else
    echo "Variables set for current session only"
    echo "Re-run this script after opening a new terminal"
fi

echo ""
echo "=== Next Steps ==="
echo "1. Test connectivity: python src/ingestion/verify_redis.py"
echo "2. Run historical backfill: python -m src.risk_engine.compute_historical_metrics"
echo ""
