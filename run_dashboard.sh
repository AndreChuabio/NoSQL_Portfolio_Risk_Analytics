#!/bin/bash
# Launch script for Streamlit dashboard
# Sets up Python path and runs the dashboard

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include project root
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Load environment variables from .zshrc or .bashrc
if [ -f ~/.zshrc ]; then
    source ~/.zshrc
elif [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# Verify credentials are set
if [ -z "$MONGODB_URI" ] || [ -z "$REDIS_HOST" ]; then
    echo "ERROR: Database credentials not found!"
    echo ""
    echo "Please add credentials to your ~/.zshrc file:"
    echo ""
    echo 'export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"'
    echo 'export REDIS_HOST="redis-xxxxx.redns.redis-cloud.com"'
    echo 'export REDIS_PORT="12345"'
    echo 'export REDIS_PASSWORD="your_redis_password"'
    echo ""
    echo "Then run: source ~/.zshrc"
    echo ""
    exit 1
fi

# Run Streamlit from project root
cd "${SCRIPT_DIR}"
echo "Starting Portfolio Risk Analytics Dashboard..."
echo "Dashboard will be available at http://localhost:8501"
streamlit run src/dashboard/app.py "$@"
