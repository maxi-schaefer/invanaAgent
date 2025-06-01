#!/bin/bash

set -e

# === Parse CLI arguments ===
for arg in "$@"; do
  case $arg in
    --token=*)
      TOKEN="${arg#*=}"
      shift
      ;;
    --serverUrl=*)
      SERVER_URL="${arg#*=}"
      shift
      ;;
    --serverPort=*)
      SERVER_PORT="${arg#*=}"
      shift
      ;;
    *)
      echo "Unknown argument: $arg"
      exit 1
      ;;
  esac
done

# === Validate required arguments ===
if [ -z "$TOKEN" ]; then
  echo "Usage: install.sh --token=<YOUR_AGENT_TOKEN> [--serverUrl=<URL>] [--serverPort=<PORT>]"
  exit 1
fi

# === Variables ===
INSTALL_DIR="/opt/invana-agent"
ZIP_URL="http://192.168.178.77:8000/invana-agent.zip"
CONFIG_FILE="$INSTALL_DIR/config.json"
PYTHON_BIN=$(which python3 || true)

echo ">> Installing invana Agent..."

# === Ensure Python 3 is installed ===
if [ -z "$PYTHON_BIN" ]; then
  echo ">> Installing Python 3..."
  apt-get update
  apt-get install -y python3 python3-pip
  PYTHON_BIN=$(which python3)
fi

# === Create install directory ===
echo ">> Creating installation directory at $INSTALL_DIR"
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# === Download and extract agent ===
echo ">> Downloading agent from $ZIP_URL"
curl -sSL "$ZIP_URL" -o /tmp/invana-agent.zip

if ! file /tmp/invana-agent.zip | grep -q 'Zip archive data'; then
  echo ">> ERROR: Downloaded file is not a valid zip archive."
  exit 1
fi

echo ">> Extracting agent..."
unzip -q /tmp/invana-agent.zip -d "$INSTALL_DIR"
rm /tmp/invana-agent.zip

# === Install Python dependencies ===
echo ">> Creating Python virtual environment..."
python3 -m venv "$INSTALL_DIR/venv"

echo ">> Activating virtual environment..."
source "$INSTALL_DIR/venv/bin/activate"

echo ">> Installing Python dependencies..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# === Write config.json ===
echo ">> Writing configuration to config.json"

cat <<EOF > "$CONFIG_FILE"
{
  "token": "$TOKEN",
  "serverUrl": "${SERVER_URL:-http://localhost}",
  "serverPort": "${SERVER_PORT:-8080}"
}
EOF

# === Set up systemd service ===
echo ">> Setting up systemd service..."
cat <<EOF > /etc/systemd/system/invana-agent.service
[Unit]
Description=invana Agent
After=network.target

[Service]
ExecStart=$INSTALL_DIR/venv/bin/python $INSTALL_DIR/agent.py
WorkingDirectory=$INSTALL_DIR
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reexec
systemctl daemon-reload
systemctl enable invana-agent
systemctl start invana-agent

echo ">> invana Agent installed successfully."
