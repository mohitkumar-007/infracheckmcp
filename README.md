# InfraHealthCheck MCP Server

Infrastructure health check suite for JungleeRummy QA environments (QA2, QA8, QA10) — exposed as an **MCP (Model Context Protocol) server** so you can run checks directly from **Claude Desktop**, **VS Code Copilot**, or any MCP-compatible client.

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

## Quick Setup

### 1. Clone the repository

```bash
git clone https://github.com/mohitkumar-007/infracheckmcp.git
cd infracheckmcp
```

### 2. Run the setup script

```bash
chmod +x setup.sh
./setup.sh
```

This creates a Python virtual environment and installs all dependencies.

---

## Using with Claude Desktop

### macOS

1. Open the Claude Desktop config file (create it if it doesn't exist):

   ```bash
   open ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

   If the file doesn't exist, create it:

   ```bash
   mkdir -p ~/Library/Application\ Support/Claude
   touch ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. Add the following configuration (replace `/FULL/PATH/TO/infracheckmcp` with the **absolute path** where you cloned the repo):

   ```json
   {
     "mcpServers": {
       "infra-health-check": {
         "command": "/FULL/PATH/TO/infracheckmcp/.venv/bin/python",
         "args": ["/FULL/PATH/TO/infracheckmcp/mcp_server.py"]
       }
     }
   }
   ```

   **Example** (if cloned to your home directory):

   ```json
   {
     "mcpServers": {
       "infra-health-check": {
         "command": "/Users/yourname/infracheckmcp/.venv/bin/python",
         "args": ["/Users/yourname/infracheckmcp/mcp_server.py"]
       }
     }
   }
   ```

### Windows

1. Open the config file at:

   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```

2. Add the configuration (use full Windows paths):

   ```json
   {
     "mcpServers": {
       "infra-health-check": {
         "command": "C:\\FULL\\PATH\\TO\\infracheckmcp\\.venv\\Scripts\\python.exe",
         "args": ["C:\\FULL\\PATH\\TO\\infracheckmcp\\mcp_server.py"]
       }
     }
   }
   ```

### Linux

1. Open or create the config file at:

   ```
   ~/.config/Claude/claude_desktop_config.json
   ```

2. Use the same JSON format as macOS with your Linux paths.

### After Configuration

3. **Restart Claude Desktop** completely (quit and reopen).
4. You should see a 🔨 (hammer) icon in the chat input — click it to confirm the infra-health-check tools are listed.
5. Ask Claude something like:

   > "Run all infra health checks for QA8"

   or

   > "Check the WebSocket health for QA2"

---

## Using with VS Code (GitHub Copilot)

The repo includes a `.vscode/mcp.json` that auto-registers the MCP server when you open this folder in VS Code.

1. Open this folder in VS Code
2. Ensure GitHub Copilot Chat extension is installed
3. The MCP tools will appear automatically in Copilot Chat

---

## Using with Claude Code (CLI)

```bash
cd infracheckmcp
claude mcp add infra-health-check .venv/bin/python mcp_server.py
```

---

## Manual / Standalone Run

You can also run the checks directly without an MCP client:

```bash
# Run all checks
.venv/bin/python run_all.py

# Start the MCP server manually (stdio mode)
.venv/bin/python mcp_server.py
```

---

## Project Structure

```
├── mcp_server.py              # MCP server — exposes TC1–TC8 as tools
├── run_all.py                 # Standalone runner for all checks
├── environments.json          # QA environment configs (servers, URLs, credentials)
├── expectedserverlist.json    # Expected server roles per environment
├── servers.json               # Server definitions
├── requirements.txt           # Python dependencies
├── setup.sh                   # One-time setup script
├── tc1_servers.py             # TC1: Server health (TCP + HTTP)
├── tc2_websocket.py           # TC2: WebSocket connectivity
├── tc3_availableserverlist.py # TC3: Server inventory validation
├── tc4_e2e_game_flow.py       # TC4: Game protocol handshake
├── tc5_wslogincheck.py        # TC5: WebSocket login
├── tc6_subscription_api.py    # TC6: Subscription API health
├── tc7_kyc_health.py          # TC7: KYC service health
├── tc8_dms_health.py          # TC8: DMS service health
└── .vscode/mcp.json           # VS Code MCP auto-registration
```

---

## Requirements

- Python 3.10+
- Network access to JungleeRummy QA environments

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Tools not appearing in Claude Desktop | Ensure you restarted Claude Desktop after editing the config. Check the path is absolute and correct. |
| `ModuleNotFoundError: mcp` | Run `./setup.sh` again, or manually: `.venv/bin/pip install -r requirements.txt` |
| Connection errors on checks | Verify you have network/VPN access to the QA environments. |
| Config file not found | Create the directory and file manually — see paths above for your OS. |
