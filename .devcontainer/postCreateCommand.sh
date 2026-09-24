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

# Display welcome message
clear
cat << 'EOF'

╔════════════════════════════════════════════════════════════╗
║        🔐 Zero-Trust OT Lab - Codespaces Ready 🔐          ║
╚════════════════════════════════════════════════════════════╝

Quick start commands:

  📦 Start lab (zero-trust mode):
     $ make up

  🏃 Start lab + attack simulation:
     $ make up
     $ make attack

  🕵️  Legacy mode (flat network - vulnerable):
     $ make legacy-up
     $ make legacy-attack

  🛑 Stop everything:
     $ make down

  📊 View gateway dashboard:
     → http://localhost:8088/dashboard

  🔗 Gateway API:
     → http://localhost:8088/api/docs

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📚 Docs:
  • Architecture:  docs/00-architecture.md
  • TP Statement:  docs/01-enonce-tp.md
  • Solution:      docs/02-corrige.md

Happy hacking! 🎯

EOF

echo ""
echo "✅ Setup complete. Run 'make up' to start the lab."
