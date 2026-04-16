# InfraHealthCheck MCP Server

Infrastructure health check suite for JungleeRummy QA environments (QA2, QA8, QA10) — exposed as an **MCP (Model Context Protocol) server**.

**Zero-clone install** — anyone can add this to Claude Desktop, Gemini CLI, or VS Code with a single config snippet. No cloning, no venv, no setup needed.

## Available Tools

| Tool | Description |
|------|-------------|
| `tc1_server_health` | Check health of all game servers (TCP + HTTP) |
| `tc2_websocket_health` | Check WebSocket connectivity to TCP game servers |
| `tc3_server_inventory` | Validate expected server roles are present |
| `tc4_game_protocol` | Test game protocol handshake (SM_INIT) |
| `tc5_ws_login` | Test WebSocket login authentication |
| `tc6_subscription_api` | Health check the Subscription Admin API |
| `tc7_kyc_service` | Health check the KYC service |
| `tc8_dms_service` | Health check the DMS service |
| `run_all_checks` | Run ALL checks (TC1–TC8) for one or all environments |

Each tool accepts an `environment` parameter: `QA2`, `QA8`, or `QA10`.

---

## Prerequisites

You need **[uv](https://docs.astral.sh/uv/getting-started/installation/)** installed (a fast Python package manager):

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

> **Note:** You also need network/VPN access to JungleeRummy QA environments for the checks to reach the servers.

---

## Claude Desktop (Recommended)

Add this to your Claude Desktop config file and **restart Claude Desktop**:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "infra-health-check": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mohitkumar-007/infracheckmcp.git", "infracheckmcp"]
    }
  }
}
```

After restarting, you'll see a 🔨 icon in the chat input. Click it to confirm the tools are loaded, then ask:

> "Run all infra health checks for QA8"

---

## Gemini CLI

Add this to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "infra-health-check": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mohitkumar-007/infracheckmcp.git", "infracheckmcp"]
    }
  }
}
```

---

## Claude Code (CLI)

```bash
claude mcp add infra-health-check -- uvx --from git+https://github.com/mohitkumar-007/infracheckmcp.git infracheckmcp
```

---

## VS Code (GitHub Copilot)

The repo includes a `.vscode/mcp.json` that auto-registers the MCP server. Just open this folder in VS Code with the Copilot Chat extension installed.

---

## Install via pip (alternative)

```bash
pip install git+https://github.com/mohitkumar-007/infracheckmcp.git
```

Then run directly:

```bash
infracheckmcp
```

---

## Project Structure

```
├── pyproject.toml                       # Package config & entry point
├── README.md
├── setup.sh                             # Dev setup script
├── requirements.txt
├── .vscode/mcp.json                     # VS Code auto-registration
└── src/infracheckmcp/
    ├── __init__.py
    ├── __main__.py                      # python -m infracheckmcp
    ├── server.py                        # MCP server (tools + resources)
    ├── run_all.py                       # Standalone runner
    ├── environments.json                # QA environment configs
    ├── expectedserverlist.json
    ├── servers.json
    ├── tc1_servers.py                   # TC1: Server health
    ├── tc2_websocket.py                 # TC2: WebSocket connectivity
    ├── tc3_availableserverlist.py       # TC3: Server inventory
    ├── tc4_e2e_game_flow.py             # TC4: Game protocol
    ├── tc5_wslogincheck.py              # TC5: WebSocket login
    ├── tc6_subscription_api.py          # TC6: Subscription API
    ├── tc7_kyc_health.py                # TC7: KYC service
    └── tc8_dms_health.py                # TC8: DMS service
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Tools not appearing | Restart Claude Desktop / Gemini CLI after editing config |
| `uvx` not found | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Connection errors | Verify VPN/network access to QA environments |
| Want to pin a version | Use `pip install git+https://...@main` with a commit hash |
