import socket
import time
import json
import os

import pymssql


def load_json(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as f:
        return json.load(f)


def check_mssql(env_name, mssql_config):
    """Check a single MSSQL instance: TCP reachability + auth + simple query."""
    ip = mssql_config["ip"]
    port = mssql_config["port"]
    database = mssql_config["database"]

    result = {
        "instance": f"{ip}:{port}",
        "database": database,
        "tcp_reachable": False,
        "authenticated": False,
        "query_ok": False,
        "latency_ms": None,
        "error": None,
    }

    # Step 1: TCP socket check
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3)
            s.connect((ip, port))
            result["tcp_reachable"] = True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        result["error"] = f"TCP connect failed: {e}"
        return result

    # Step 2: MSSQL connection + auth + query
    try:
        start = time.perf_counter()
        conn = pymssql.connect(
            server=ip,
            port=str(port),
            user=mssql_config["username"],
            password=mssql_config["password"],
            database=database,
            login_timeout=5,
            tds_version="7.3",
        )
        result["authenticated"] = True

        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        row = cursor.fetchone()
        latency = round((time.perf_counter() - start) * 1000)
        result["latency_ms"] = latency

        if row and row[0] == 1:
            result["query_ok"] = True

        cursor.close()
        conn.close()
    except pymssql.OperationalError as e:
        result["error"] = f"Connection/auth failed: {e}"
    except pymssql.InterfaceError as e:
        result["error"] = f"Interface error: {e}"
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"

    return result


def run_tc11(env_name, env_config):
    mssql_config = env_config.get("mssql")
    if not mssql_config:
        print(f"  ⚠️  No mssql configured for {env_name} — skipping TC11.")
        return {"env": env_name, "test": "TC11", "status": "SKIPPED", "mssql_health": {}}

    print(f"\n{'=' * 70}")
    print(f"  [{env_name}] MSSQL — Health Check")
    print(f"  Server: {mssql_config['ip']}:{mssql_config['port']}  |  DB: {mssql_config['database']}")
    print(f"{'=' * 70}")

    r = check_mssql(env_name, mssql_config)

    print(f"\n  {'CHECK':<20} | {'RESULT':<8}")
    print("  " + "-" * 32)

    tcp_icon = "✅" if r["tcp_reachable"] else "❌"
    auth_icon = "✅" if r["authenticated"] else "❌"
    query_icon = "✅" if r["query_ok"] else "❌"
    latency = f"{r['latency_ms']}ms" if r["latency_ms"] is not None else "N/A"

    print(f"  {'TCP Reachable':<20} | {tcp_icon}")
    print(f"  {'Authenticated':<20} | {auth_icon}")
    print(f"  {'SELECT 1 Query':<20} | {query_icon}  ({latency})")

    if r["error"]:
        print(f"    ⚠️  {r['error']}")

    status = "PASS" if r["query_ok"] else "FAILED"
    checks_passed = sum([r["tcp_reachable"], r["authenticated"], r["query_ok"]])

    print(f"\n  ──────────────────────────────────────────────────")
    print(f"  [{env_name}] Result: {status}  ({checks_passed}/3 checks passed)")

    return {
        "env": env_name,
        "test": "TC11",
        "status": status,
        "summary": f"MSSQL {mssql_config['database']} — {checks_passed}/3 checks passed",
        "mssql_health": r,
    }


if __name__ == "__main__":
    envs = load_json('environments.json')
    for env_name, env_config in envs.items():
        result = run_tc11(env_name, env_config)
        print(json.dumps(result, indent=2))
