#!/bin/bash
# One-time setup for InfraHealthCheck MCP server
set -e

cd "$(dirname "$0")"

echo "🔧 Creating virtual environment..."
python3 -m venv .venv

echo "📦 Installing dependencies..."
.venv/bin/pip install -r requirements.txt --quiet

echo ""
echo "✅ Setup complete!"
echo ""
echo "  VS Code users: The MCP server will be auto-detected via .vscode/mcp.json"
echo "  Just open this folder in VS Code and Copilot can use the infra health tools."
echo ""
echo "  Manual run:  .venv/bin/python run_all.py"
echo "  MCP server:  .venv/bin/python mcp_server.py"
