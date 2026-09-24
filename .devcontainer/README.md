# Codespaces Configuration

This folder contains the Codespaces devcontainer configuration to run the **Zero-Trust OT Lab** directly in the cloud.

## What's included

- **Docker-in-Docker**: Full Docker Compose support with isolated networks
- **Python tools**: Pre-configured for testing and development
- **VS Code extensions**: Docker, Ruff (Python linter), Python support
- **Port forwarding**: Automatic forwarding for gateway (8088) and PLC (8081)

## Getting Started

### 1. Create Codespace

On GitHub (your repo):
```
Code → Codespaces → Create codespace on main
```

The devcontainer will auto-setup in ~2 minutes.

### 2. Run the Lab

```bash
# Zero-Trust mode (default)
make up

# Run attack simulation in a second terminal
make attack

# View live dashboard
# → http://localhost:8088/dashboard
```

### 3. Clean up

```bash
make down
```

## Available Make targets

```bash
make up              # Start zero-trust lab
make down            # Stop everything
make attack          # Run attacker (requires 'make up' first)
make legacy-up       # Start legacy flat-network mode
make legacy-attack   # Attack legacy mode
make logs            # Tail gateway logs
```

## Tips

- **Two terminals**: Use one for `make up`, another for `make attack`
- **Dashboard**: Visit http://localhost:8088/dashboard to see real-time audit logs
- **Docs**: Read `docs/00-architecture.md` for network topology details

## Troubleshooting

If Docker fails to start:
```bash
# Restart Docker daemon
sudo service docker restart

# Check status
docker ps
```

If services don't start:
```bash
# View logs
docker compose logs -f gateway

# Rebuild images
docker compose down
docker compose up --build
```
