#!/bin/bash
# Launch script for Streamlit dashboard
# Sets up Python path and runs the dashboard

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include project root
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Load environment variables
if [ -f "${SCRIPT_DIR}/setup_env.sh" ]; then
    source "${SCRIPT_DIR}/setup_env.sh"
fi

# Run Streamlit from project root
cd "${SCRIPT_DIR}"
echo "Starting Portfolio Risk Analytics Dashboard..."
echo "Dashboard will be available at http://localhost:8501"
streamlit run src/dashboard/app.py "$@"
