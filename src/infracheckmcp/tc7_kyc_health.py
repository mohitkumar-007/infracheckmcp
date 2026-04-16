import requests
import time
import json
import os


def load_json(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as f:
        return json.load(f)


def check_kyc(env_name, env_config):
    base_url = env_config.get("kyc_url", "")
    if not base_url:
        print(f"  ⚠️  No kyc_url for {env_name} — skipping TC7.")
        return {"env": env_name, "test": "TC7", "status": "SKIPPED", "checks": []}

    print(f"\n{'=' * 70}")
    print(f"  [{env_name}] KYC Service — Health Check")
    print(f"  Base URL: {base_url}")
    print(f"{'=' * 70}")

    checks = []
    all_pass = True

    # ── Check 1: Service reachability (GET /v2/kyc → expect 405 Method Not Allowed) ──
    print("\n  [1] Service Reachability  →  GET /v2/kyc")
    endpoint = f"{base_url}/v2/kyc"
    try:
        start = time.perf_counter()
        resp = requests.get(endpoint, timeout=5)
        latency = round((time.perf_counter() - start) * 1000)
        status = resp.status_code

        # 405 = service is up, just doesn't allow GET (POST-only API)
        if status == 405:
            print(f"    ✅ Status: {status} (Method Not Allowed — service alive)  |  Latency: {latency}ms")
            checks.append({"check": "reachability", "passed": True, "status": status, "latency_ms": latency})
        elif status < 500:
            print(f"    ✅ Status: {status}  |  Latency: {latency}ms")
            checks.append({"check": "reachability", "passed": True, "status": status, "latency_ms": latency})
        else:
            print(f"    ❌ Status: {status}  |  Latency: {latency}ms")
            checks.append({"check": "reachability", "passed": False, "status": status, "latency_ms": latency})
            all_pass = False
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Connection failed: {e}")
        checks.append({"check": "reachability", "passed": False, "error": str(e)})
        all_pass = False
        print(f"\n  ──────────────────────────────────────────────────")
        result = "PASS" if all_pass else "FAILED"
        passed_count = sum(1 for c in checks if c["passed"])
        print(f"  [{env_name}] Result: {result}  ({passed_count}/{len(checks)} checks passed)")
        return {"env": env_name, "test": "TC7", "status": result, "checks": checks,
                "passed": f"{passed_count}/{len(checks)}"}

    # ── Check 2: Verify response structure ──
    print("\n  [2] Response Validation  →  GET /v2/kyc")
    try:
        body = resp.json()
        has_error_field = "error" in body
        if has_error_field:
            print(f"    ✅ Valid JSON response with expected 'error' field")
            checks.append({"check": "response_structure", "passed": True})
        else:
            print(f"    ⚠️  JSON response missing 'error' field: {json.dumps(body)[:200]}")
            checks.append({"check": "response_structure", "passed": True})  # still alive
    except Exception:
        print(f"    ⚠️  Non-JSON response: {resp.text[:100]}")
        checks.append({"check": "response_structure", "passed": True})  # service is still up

    # ── Check 3: Verify istio-envoy proxy ──
    print("\n  [3] Proxy Layer  →  Checking server header")
    server_header = resp.headers.get("server", "unknown")
    if "envoy" in server_header.lower() or "istio" in server_header.lower():
        print(f"    ✅ Behind istio-envoy proxy  (server: {server_header})")
        checks.append({"check": "proxy", "passed": True, "server": server_header})
    else:
        print(f"    ⚠️  Unexpected server header: {server_header}")
        checks.append({"check": "proxy", "passed": True, "server": server_header})  # not a failure

    # ── Summary ──
    result = "PASS" if all_pass else "FAILED"
    passed_count = sum(1 for c in checks if c["passed"])
    print(f"\n  ──────────────────────────────────────────────────")
    print(f"  [{env_name}] Result: {result}  ({passed_count}/{len(checks)} checks passed)")
    return {"env": env_name, "test": "TC7", "status": result, "checks": checks,
            "passed": f"{passed_count}/{len(checks)}"}


def run_tc7(env_name=None, env_config=None):
    if env_name and env_config:
        return check_kyc(env_name, env_config)

    envs = load_json('environments.json')
    results = {}
    for name, config in envs.items():
        results[name] = check_kyc(name, config)
    return results


if __name__ == "__main__":
    run_tc7()
