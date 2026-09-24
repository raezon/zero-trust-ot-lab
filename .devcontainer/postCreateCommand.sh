#!/bin/bash
set -e

echo "🚀 Setting up Zero-Trust OT Lab..."

# Install system dependencies
apt-get update
apt-get install -y \
    make \
    curl \
    git \
    python3-pip \
    > /dev/null 2>&1

# Install Python dependencies for tests (optional)
if [ -f "tests/requirements.txt" ]; then
    pip3 install -q -r tests/requirements.txt
fi

# 🚀 Auto-start the lab in background
echo "🚀 Starting Zero-Trust OT Lab services in background..."
docker compose up -d > /tmp/compose.log 2>&1 &
COMPOSE_PID=$!

# Wait a bit for services to start initializing
sleep 5

# Display welcome message
clear
cat << 'EOF'

╔════════════════════════════════════════════════════════════╗
║     🔐 Zero-Trust OT Lab - AUTO-STARTING 🔐                ║
║                                                            ║
║     Services launching in background...                   ║
╚════════════════════════════════════════════════════════════╝

⏳ STATUS: Starting (check below)

Check if services are ready:
  $ docker compose ps
  $ docker compose logs -f gateway

🌐 WHEN READY (usually 30-60 seconds):
  📊 Dashboard:    http://localhost:8088/dashboard
  🔗 API Docs:     http://localhost:8088/api/docs
  ⚙️  Gateway:      http://localhost:8088/command

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Run attack simulation (once services are ready):
  $ make attack

Stop all services:
  $ make down

Restart services:
  $ docker compose restart

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 Documentation:
  • Architecture:  docs/00-architecture.md
  • TP Statement:  docs/01-enonce-tp.md
  • Solution:      docs/02-corrige.md

Happy hacking! 🎯

EOF

echo ""
echo "💡 Tip: Run 'docker compose ps' to see service status"
