"""
InfraHealthCheck MCP Server
============================
Exposes infrastructure health check test cases (TC1–TC8) as MCP tools
so they can be called from any AI interface (VS Code Copilot, Claude, etc.).

Run:  infracheckmcp
  or: python -m infracheckmcp
  or: uvx infracheckmcp
"""

import asyncio
import json
import io
import os
from contextlib import redirect_stdout

from mcp.server.fastmcp import FastMCP

from infracheckmcp.tc1_servers import run_tc1
from infracheckmcp.tc2_websocket import run_tc2
from infracheckmcp.tc3_availableserverlist import run_tc3
from infracheckmcp.tc4_e2e_game_flow import run_tc4
from infracheckmcp.tc5_wslogincheck import run_tc5
from infracheckmcp.tc6_subscription_api import run_tc6
from infracheckmcp.tc7_kyc_health import run_tc7
from infracheckmcp.tc8_dms_health import run_tc8

mcp = FastMCP(
    "InfraHealthCheck",
    instructions="Infrastructure health check suite for JungleeRummy QA environments (QA2, QA8, QA10). Use the tools to check server health, WebSocket connectivity, game protocols, login, subscription API, KYC, and DMS services.",
)

# ── Helpers ──────────────────────────────────────────────────────────

def _load_envs():
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "environments.json")
    with open(env_path, "r") as f:
        return json.load(f)


def _resolve_env(environment: str):
    """Return (env_name, env_config) or raise ValueError."""
    envs = _load_envs()
    key = environment.upper()
    if key not in envs:
        available = ", ".join(envs.keys())
        raise ValueError(f"Unknown environment '{environment}'. Available: {available}")
    return key, envs[key]


def _capture_output(fn, *args, **kwargs):
    """Run a function and capture its stdout alongside the return value."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = fn(*args, **kwargs)
    return result, buf.getvalue()


def _capture_output_async(coro):
    """Run an async coroutine and capture its stdout alongside the return value."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = asyncio.run(coro)
    return result, buf.getvalue()


def _format_result(result: dict, output: str) -> str:
    """Format a TC result into a readable string."""
    status = result.get("overall_status", result.get("status", "UNKNOWN"))
    summary = result.get("summary", result.get("passed", ""))
    lines = [f"Status: {status}"]
    if summary:
        lines.append(f"Summary: {summary}")
    if output.strip():
        lines.append(f"\nDetailed Output:\n{output.strip()}")
    return "\n".join(lines)


# ── Individual TC Tools ──────────────────────────────────────────────

@mcp.tool()
def tc1_server_health(environment: str) -> str:
    """Check health of all game servers (TCP socket + HTTP) for a QA environment.

    Args:
        environment: QA environment name (QA2, QA8, or QA10)
    """
    env_name, env_config = _resolve_env(environment)
    result, output = _capture_output(run_tc1, env_name, env_config)
    return _format_result(result, output)


@mcp.tool()
def tc2_websocket_health(environment: str) -> str:
    """Check WebSocket connectivity to TCP game servers via the WS gateway.

    Args:
        environment: QA environment name (QA2, QA8, or QA10)
    """
    env_name, env_config = _resolve_env(environment)
    result, output = _capture_output_async(run_tc2(env_name, env_config))
    return _format_result(result, output)


@mcp.tool()
def tc3_server_inventory(environment: str) -> str:
    """Validate that all expected server roles are present in the environment config.

    Args:
        environment: QA environment name (QA2, QA8, or QA10)
    """
    env_name, env_config = _resolve_env(environment)
    result, output = _capture_output(run_tc3, env_name, env_config)
    return _format_result(result, output)


@mcp.tool()
def tc4_game_protocol(environment: str) -> str:
    """Test game protocol handshake (SM_INIT) on TCP game servers via WS gateway.

    Args:
        environment: QA environment name (QA2, QA8, or QA10)
    """
    env_name, env_config = _resolve_env(environment)
    result, output = _capture_output_async(run_tc4(env_name, env_config))
    return _format_result(result, output)


@mcp.tool()
def tc5_ws_login(environment: str) -> str:
    """Test WebSocket login authentication (sends credentials, waits for sm-login-success).

    Args:
        environment: QA environment name (QA2, QA8, or QA10)
    """
    env_name, env_config = _resolve_env(environment)
    result, output = _capture_output_async(run_tc5(env_name, env_config))
    return _format_result(result, output)


@mcp.tool()
def tc6_subscription_api(environment: str) -> str:
    """Health check the Subscription Admin API (tabs, eligible passes for Tournament/Gems/Coins).

    Args:
        environment: QA environment name (QA2, QA8, or QA10)
    """
    env_name, env_config = _resolve_env(environment)
    result, output = _capture_output(run_tc6, env_name, env_config)
    return _format_result(result, output)


@mcp.tool()
def tc7_kyc_service(environment: str) -> str:
    """Health check the KYC service (reachability, response validation, proxy layer).

    Args:
        environment: QA environment name (QA2, QA8, or QA10)
    """
    env_name, env_config = _resolve_env(environment)
    result, output = _capture_output(run_tc7, env_name, env_config)
    return _format_result(result, output)


@mcp.tool()
def tc8_dms_service(environment: str) -> str:
    """Health check the DMS service (reachability, response validation, proxy layer).

    Args:
        environment: QA environment name (QA2, QA8, or QA10)
    """
    env_name, env_config = _resolve_env(environment)
    result, output = _capture_output(run_tc8, env_name, env_config)
    return _format_result(result, output)


# ── Run All Tool ─────────────────────────────────────────────────────

@mcp.tool()
def run_all_checks(environment: str = "all") -> str:
    """Run ALL health checks (TC1-TC8) for one or all QA environments.

    Args:
        environment: QA environment name (QA2, QA8, QA10) or "all" for every environment
    """
    envs = _load_envs()
    if environment.lower() != "all":
        key, _ = _resolve_env(environment)
        envs = {key: envs[key]}

    tc_runners = [
        ("TC1: Server Health",       lambda n, c: _capture_output(run_tc1, n, c)),
        ("TC2: WebSocket Health",    lambda n, c: _capture_output_async(run_tc2(n, c))),
        ("TC3: Server Inventory",    lambda n, c: _capture_output(run_tc3, n, c)),
        ("TC4: Game Protocol",       lambda n, c: _capture_output_async(run_tc4(n, c))),
        ("TC5: WS Login",           lambda n, c: _capture_output_async(run_tc5(n, c))),
        ("TC6: Subscription API",    lambda n, c: _capture_output(run_tc6, n, c)),
        ("TC7: KYC Service",         lambda n, c: _capture_output(run_tc7, n, c)),
        ("TC8: DMS Service",         lambda n, c: _capture_output(run_tc8, n, c)),
    ]

    lines = []
    summary_rows = []

    for env_name, env_config in envs.items():
        lines.append(f"\n{'=' * 60}")
        lines.append(f"  ENVIRONMENT: {env_name}")
        lines.append(f"{'=' * 60}")

        env_statuses = []
        for tc_label, runner in tc_runners:
            try:
                result, output = runner(env_name, env_config)
                status = result.get("overall_status", result.get("status", "UNKNOWN"))
                summary = result.get("summary", result.get("passed", ""))
                icon = "PASS" if status == "PASS" else ("SKIP" if status == "SKIPPED" else "FAIL")
                lines.append(f"  {icon:6s} | {tc_label:25s} | {summary}")
                env_statuses.append(status)
            except Exception as e:
                lines.append(f"  ERROR | {tc_label:25s} | {str(e)[:80]}")
                env_statuses.append("FAILED")

        env_pass = all(s in ("PASS", "SKIPPED") for s in env_statuses)
        summary_rows.append((env_name, env_statuses, env_pass))

    # Grand summary table
    lines.append(f"\n{'=' * 60}")
    lines.append("  GRAND SUMMARY")
    lines.append(f"{'=' * 60}")
    tc_short = ["TC1", "TC2", "TC3", "TC4", "TC5", "TC6", "TC7", "TC8"]
    header = f"  {'ENV':<6}" + "".join(f" {t:<6}" for t in tc_short) + "  OVERALL"
    lines.append(header)
    lines.append("  " + "-" * (6 + 7 * len(tc_short) + 10))
    for env_name, statuses, env_pass in summary_rows:
        row = f"  {env_name:<6}"
        for s in statuses:
            tag = "PASS" if s == "PASS" else ("SKIP" if s == "SKIPPED" else "FAIL")
            row += f" {tag:<6}"
        row += f"  {'PASS' if env_pass else 'FAIL'}"
        lines.append(row)

    return "\n".join(lines)


# ── Resources ────────────────────────────────────────────────────────

@mcp.resource("config://environments")
def get_environments() -> str:
    """Return the current environments.json configuration."""
    return json.dumps(_load_envs(), indent=2)


@mcp.resource("config://environments/{env_name}")
def get_environment(env_name: str) -> str:
    """Return the configuration for a specific environment."""
    envs = _load_envs()
    key = env_name.upper()
    if key not in envs:
        return json.dumps({"error": f"Unknown environment: {env_name}", "available": list(envs.keys())})
    return json.dumps(envs[key], indent=2)


# ── Entry Point ──────────────────────────────────────────────────────

def main():
    """CLI entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
