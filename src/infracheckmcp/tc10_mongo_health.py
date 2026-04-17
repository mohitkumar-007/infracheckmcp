import socket
import time
import json
import os

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure


def load_json(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as f:
        return json.load(f)


def check_mongo(instance):
    """Check a single MongoDB instance: TCP reachability + auth + ping."""
    name = instance["name"]
    ip = instance["ip"]
    port = instance["port"]

    result = {
        "instance": name,
        "host": f"{ip}:{port}",
        "tcp_reachable": False,
        "authenticated": False,
        "ping_ok": False,
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

    # Step 2: MongoDB connection + auth + ping
    uri = (
        f"mongodb://{instance['username']}:{instance['password']}"
        f"@{ip}:{port}/?authMechanism={instance['auth_mechanism']}"
    )
    try:
        start = time.perf_counter()
        client = MongoClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=3000)
        # Force connection + auth by issuing a ping
        client.admin.command("ping")
        latency = round((time.perf_counter() - start) * 1000)

        result["authenticated"] = True
        result["ping_ok"] = True
        result["latency_ms"] = latency
        client.close()
    except ConnectionFailure as e:
        result["error"] = f"Connection/auth failed: {e}"
    except OperationFailure as e:
        result["error"] = f"Auth failed: {e}"
    except Exception as e:
        result["error"] = f"Unexpected error: {e}"

    return result


def run_tc10(env_name, env_config):
    instances = env_config.get("mongo_instances", [])
    if not instances:
        print(f"  ⚠️  No mongo_instances configured for {env_name} — skipping TC10.")
        return {"env": env_name, "test": "TC10", "status": "SKIPPED", "mongo_health": []}

    print(f"\n{'=' * 70}")
    print(f"  [{env_name}] MongoDB — Health Check")
    print(f"{'=' * 70}")
    print(f"\n  {'INSTANCE':<20} | {'TCP':<6} | {'AUTH':<6} | {'PING':<6} | {'LATENCY':<10}")
    print("  " + "-" * 60)

    mongo_results = []
    for inst in instances:
        r = check_mongo(inst)
        mongo_results.append(r)

        tcp_icon = "✅" if r["tcp_reachable"] else "❌"
        auth_icon = "✅" if r["authenticated"] else "❌"
        ping_icon = "✅" if r["ping_ok"] else "❌"
        latency = f"{r['latency_ms']}ms" if r["latency_ms"] is not None else "N/A"
        print(f"  {r['instance']:<20} | {tcp_icon:<6} | {auth_icon:<6} | {ping_icon:<6} | {latency:<10}")
        if r["error"]:
            print(f"    ⚠️  {r['error']}")

    passed = sum(1 for r in mongo_results if r["ping_ok"])
    total = len(mongo_results)
    status = "PASS" if passed == total else "FAILED"

    print(f"\n  ──────────────────────────────────────────────────")
    print(f"  [{env_name}] Result: {status}  ({passed}/{total} instances healthy)")

    return {
        "env": env_name,
        "test": "TC10",
        "status": status,
        "summary": f"{passed}/{total} MongoDB instances healthy",
        "mongo_health": mongo_results,
    }


if __name__ == "__main__":
    envs = load_json('environments.json')
    for env_name, env_config in envs.items():
        result = run_tc10(env_name, env_config)
        print(json.dumps(result, indent=2))
