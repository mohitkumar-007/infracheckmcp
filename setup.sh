#!/bin/bash
# One-time setup for InfraHealthCheck MCP server
set -e

cd "$(dirname "$0")"

echo "🔧 Creating virtual environment..."
python3 -m venv .venv

echo "📦 Installing dependencies..."
.venv/bin/pip install -r requirements.txt --quiet

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo "✅ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  VS Code (Copilot):"
echo "    The MCP server will be auto-detected via .vscode/mcp.json"
echo "    Just open this folder in VS Code."
echo ""
echo "  Claude Desktop:"
echo "    Add this to your Claude Desktop config file:"
echo ""
echo "    macOS:  ~/Library/Application Support/Claude/claude_desktop_config.json"
echo "    Windows: %APPDATA%\\Claude\\claude_desktop_config.json"
echo "    Linux:  ~/.config/Claude/claude_desktop_config.json"
echo ""
echo "    {"
echo "      \"mcpServers\": {"
echo "        \"infra-health-check\": {"
echo "          \"command\": \"${PROJECT_DIR}/.venv/bin/python\","
echo "          \"args\": [\"${PROJECT_DIR}/mcp_server.py\"]"
echo "        }"
echo "      }"
echo "    }"
echo ""
echo "    Then restart Claude Desktop."
echo ""
echo "  Claude Code (CLI):"
echo "    claude mcp add infra-health-check .venv/bin/python mcp_server.py"
echo ""
echo "  Manual run:  .venv/bin/python run_all.py"
echo "  MCP server:  .venv/bin/python mcp_server.py"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
