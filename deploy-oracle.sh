#!/bin/bash
set -e

echo "🚀 Zero-Trust OT Lab — Deployment on Oracle Cloud Always Free"
echo "=============================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}ℹ️ $1${NC}"; }
log_ok() { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️ $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; exit 1; }

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    log_warn "This script should be run as 'ubuntu' user"
fi

# Step 1: Update system
log_info "Step 1/5: Updating system packages..."
sudo apt-get update > /dev/null
sudo apt-get upgrade -y > /dev/null
log_ok "System updated"

# Step 2: Install Docker
log_info "Step 2/5: Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh > /dev/null 2>&1
    sudo usermod -aG docker ubuntu
    log_ok "Docker installed"
else
    log_ok "Docker already installed"
fi

# Step 3: Install Docker Compose & tools
log_info "Step 3/5: Installing Docker Compose and tools..."
sudo apt-get install -y docker-compose-plugin git make curl wget > /dev/null 2>&1
log_ok "Tools installed"

# Step 4: Clone repository
log_info "Step 4/5: Cloning Zero-Trust OT Lab..."
REPO_DIR="$HOME/zero-trust-ot-lab"
if [ ! -d "$REPO_DIR" ]; then
    git clone https://github.com/raezon/zero-trust-ot-lab.git "$REPO_DIR"
    log_ok "Repository cloned"
else
    log_warn "Repository already exists, pulling latest..."
    cd "$REPO_DIR" && git pull
fi

cd "$REPO_DIR"

# Step 5: Start services
log_info "Step 5/5: Starting Docker Compose services..."
docker compose up -d > /dev/null 2>&1

# Wait for services to be ready
log_info "Waiting for services to start (30 seconds)..."
sleep 30

# Verify services
if docker compose ps | grep -q "healthy\|Up"; then
    log_ok "Services started successfully!"
else
    log_warn "Services may still be starting, checking logs..."
fi

echo ""
echo "=============================================================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "=============================================================="
echo ""

# Display status
log_info "Services status:"
docker compose ps

echo ""
log_info "Dashboard accessible locally:"
echo "  http://localhost:8088/dashboard"
echo "  http://localhost:8088/"
echo ""

# Install Cloudflare Tunnel
log_info "Installing Cloudflare Tunnel for public access..."
if ! command -v cloudflared &> /dev/null; then
    curl -L https://pkg.cloudflare.com/cloudflare-linux.gpg | sudo tee /etc/apt/trusted.gpg.d/cloudflare.gpg > /dev/null
    echo 'deb [signed-by=/etc/apt/trusted.gpg.d/cloudflare.gpg] https://pkg.cloudflare.com/linux focal main' | sudo tee /etc/apt/sources.list.d/cloudflare.list > /dev/null
    sudo apt-get update > /dev/null
    sudo apt-get install -y cloudflared > /dev/null 2>&1
    log_ok "Cloudflare Tunnel installed"
else
    log_ok "Cloudflare Tunnel already installed"
fi

echo ""
echo "=============================================================="
echo -e "${YELLOW}📡 NEXT STEP: Expose with Cloudflare Tunnel${NC}"
echo "=============================================================="
echo ""
echo "To make the lab publicly accessible, run:"
echo ""
echo -e "${BLUE}cloudflared tunnel run --url http://localhost:8088${NC}"
echo ""
echo "This will give you a public HTTPS URL like:"
echo "  https://my-tunnel.trycloudflare.com"
echo ""
echo "Keep this terminal open for the tunnel to stay active."
echo ""

# Optional: Create systemd service for auto-start
log_info "Creating systemd service for auto-start..."
cat > /tmp/zero-trust-ot.service << 'EOF'
[Unit]
Description=Zero-Trust OT Lab
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/zero-trust-ot-lab
ExecStart=/usr/bin/docker compose up
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

log_info "Service file created at /tmp/zero-trust-ot.service"
log_info "To enable auto-start on VM reboot, run:"
echo -e "${BLUE}sudo cp /tmp/zero-trust-ot.service /etc/systemd/system/${NC}"
echo -e "${BLUE}sudo systemctl daemon-reload${NC}"
echo -e "${BLUE}sudo systemctl enable zero-trust-ot${NC}"
echo ""

echo "=============================================================="
echo -e "${GREEN}✨ Deployment Summary${NC}"
echo "=============================================================="
echo "✅ Docker installed and configured"
echo "✅ Lab services running (docker compose up -d)"
echo "✅ Cloudflare Tunnel ready for public access"
echo ""
echo "📊 Dashboard:"
echo "  Local:  http://localhost:8088/dashboard"
echo "  Public: Run 'cloudflared tunnel run --url http://localhost:8088'"
echo ""
echo "📝 Useful commands:"
echo "  docker compose ps          # Check services status"
echo "  docker compose logs -f     # View live logs"
echo "  docker compose down        # Stop all services"
echo "  make attack               # Run attack scenario"
echo ""
echo "🔗 Repository: https://github.com/raezon/zero-trust-ot-lab"
echo ""
