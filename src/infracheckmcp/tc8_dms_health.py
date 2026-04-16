import requests
import time
import json
import os
import urllib3

# Suppress InsecureRequestWarning for self-signed certs in QA
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def load_json(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as f:
        return json.load(f)


def check_dms(env_name, env_config):
    base_url = env_config.get("dms_url", "")
    if not base_url:
        print(f"  ⚠️  No dms_url for {env_name} — skipping TC8.")
        return {"env": env_name, "test": "TC8", "status": "SKIPPED", "checks": []}

    print(f"\n{'=' * 70}")
    print(f"  [{env_name}] DMS Service — Health Check")
    print(f"  Base URL: {base_url}")
    print(f"{'=' * 70}")

    checks = []
    all_pass = True

    # ── Check 1: Service reachability (GET /v2 → expect non-5xx or 405) ──
    print("\n  [1] Service Reachability  →  GET /v2")
    endpoint = f"{base_url}/v2"
    try:
        start = time.perf_counter()
        resp = requests.get(endpoint, timeout=5, verify=False)
        latency = round((time.perf_counter() - start) * 1000)
        status = resp.status_code

        if status == 503:
            print(f"    ❌ Status: {status} — no healthy upstream  |  Latency: {latency}ms")
            checks.append({"check": "reachability", "passed": False, "status": status, "latency_ms": latency})
            all_pass = False
        elif status >= 500:
            print(f"    ❌ Status: {status}  |  Latency: {latency}ms")
            checks.append({"check": "reachability", "passed": False, "status": status, "latency_ms": latency})
            all_pass = False
        elif status == 405:
            print(f"    ✅ Status: {status} (Method Not Allowed — service alive)  |  Latency: {latency}ms")
            checks.append({"check": "reachability", "passed": True, "status": status, "latency_ms": latency})
        else:
            print(f"    ✅ Status: {status}  |  Latency: {latency}ms")
            checks.append({"check": "reachability", "passed": True, "status": status, "latency_ms": latency})
    except requests.exceptions.RequestException as e:
        err_msg = str(e)
        if "NameResolution" in err_msg or "nodename" in err_msg:
            print(f"    ❌ DNS resolution failed for {base_url}")
        else:
            print(f"    ❌ Connection failed: {err_msg[:150]}")
        checks.append({"check": "reachability", "passed": False, "error": err_msg[:200]})
        all_pass = False
        # Can't continue if service is unreachable
        result = "FAILED"
        print(f"\n  ──────────────────────────────────────────────────")
        print(f"  [{env_name}] Result: {result}  (0/1 checks passed)")
        return {"env": env_name, "test": "TC8", "status": result, "checks": checks,
                "passed": "0/1"}

    # ── Check 2: Response validation ──
    print("\n  [2] Response Validation  →  GET /v2")
    try:
        body = resp.json()
        print(f"    ✅ Valid JSON response: {json.dumps(body)[:150]}")
        checks.append({"check": "response_structure", "passed": True})
    except Exception:
        body_text = resp.text[:100]
        if status < 500:
            print(f"    ⚠️  Non-JSON response: {body_text}")
            checks.append({"check": "response_structure", "passed": True})
        else:
            print(f"    ❌ Non-JSON error response: {body_text}")
            checks.append({"check": "response_structure", "passed": False})
            all_pass = False

    # ── Check 3: Proxy layer ──
    print("\n  [3] Proxy Layer  →  Checking server header")
    server_header = resp.headers.get("server", "unknown")
    if "envoy" in server_header.lower() or "istio" in server_header.lower():
        print(f"    ✅ Behind istio-envoy proxy  (server: {server_header})")
    else:
        print(f"    ℹ️  Server header: {server_header}")
    checks.append({"check": "proxy", "passed": True, "server": server_header})

    # ── Summary ──
    result = "PASS" if all_pass else "FAILED"
    passed_count = sum(1 for c in checks if c["passed"])
    print(f"\n  ──────────────────────────────────────────────────")
    print(f"  [{env_name}] Result: {result}  ({passed_count}/{len(checks)} checks passed)")
    return {"env": env_name, "test": "TC8", "status": result, "checks": checks,
            "passed": f"{passed_count}/{len(checks)}"}


def run_tc8(env_name=None, env_config=None):
    if env_name and env_config:
        return check_dms(env_name, env_config)

    envs = load_json('environments.json')
    results = {}
    for name, config in envs.items():
        results[name] = check_dms(name, config)
    return results


if __name__ == "__main__":
    run_tc8()
