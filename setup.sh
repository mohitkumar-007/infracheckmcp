#!/bin/bash
# One-time setup for InfraHealthCheck MCP server (for local development)
set -e

cd "$(dirname "$0")"

echo "🔧 Creating virtual environment..."
python3 -m venv .venv

echo "📦 Installing package in editable mode..."
.venv/bin/pip install -e . --quiet

echo ""
echo "✅ Setup complete!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Anyone can install this MCP with a single config — NO cloning needed!"
echo ""
echo "  Claude Desktop  →  add to claude_desktop_config.json:"
echo ""
echo '    {'
echo '      "mcpServers": {'
echo '        "infra-health-check": {'
echo '          "command": "uvx",'
echo '          "args": ["--from", "git+https://github.com/mohitkumar-007/infracheckmcp.git", "infracheckmcp"]'
echo '        }'
echo '      }'
echo '    }'
echo ""
echo "  Gemini CLI  →  add to ~/.gemini/settings.json:"
echo ""
echo '    {'
echo '      "mcpServers": {'
echo '        "infra-health-check": {'
echo '          "command": "uvx",'
echo '          "args": ["--from", "git+https://github.com/mohitkumar-007/infracheckmcp.git", "infracheckmcp"]'
echo '        }'
echo '      }'
echo '    }'
echo ""
echo "  Claude Code CLI:"
echo '    claude mcp add infra-health-check -- uvx --from git+https://github.com/mohitkumar-007/infracheckmcp.git infracheckmcp'
echo ""
echo "  VS Code (Copilot):"
echo "    Just open this folder in VS Code — auto-detected via .vscode/mcp.json"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
