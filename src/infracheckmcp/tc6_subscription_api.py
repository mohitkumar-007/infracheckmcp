import requests
import json
import time
import os

def load_json(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as f:
        return json.load(f)

# Target pass types to validate
TARGET_PASS_TYPES = ["tournament", "gems", "coins"]


def api_get(base_url, path, params=None):
    """Call a GET endpoint and return (status_code, json_body, latency_ms, error)."""
    url = f"{base_url}{path}"
    try:
        start = time.perf_counter()
        resp = requests.get(url, params=params, timeout=10)
        latency = round((time.perf_counter() - start) * 1000)
        try:
            body = resp.json()
        except Exception:
            body = resp.text[:500]
        return resp.status_code, body, latency, None
    except requests.exceptions.ConnectionError as e:
        return None, None, None, f"Connection failed: {e}"
    except requests.exceptions.Timeout:
        return None, None, None, "Request timed out (10s)"
    except requests.exceptions.RequestException as e:
        return None, None, None, str(e)


def check_environment(env_name, env_config):
    base_url = env_config.get("subscription_admin_url", "")
    if not base_url:
        print(f"  ⚠️  No subscription_admin_url for {env_name} — skipping TC6.")
        return {"env": env_name, "test": "TC6", "overall_status": "SKIPPED", "results": []}

    print(f"\n{'=' * 70}")
    print(f"  [{env_name}] Subscription Admin API — Health Check")
    print(f"  Base URL: {base_url}")
    print(f"{'=' * 70}")

    results = []

    # ── Step 1: Service reachability (actuator) ──
    print("\n  [1] Actuator Health")
    code, body, lat, err = api_get(base_url, "/actuator/health")
    actuator_ok = code == 200
    icon = "✅" if actuator_ok else "❌"
    print(f"    {icon} /actuator/health  [{code or 'N/A'}]  {lat or 0}ms")
    if err:
        print(f"       ⚠️  {err}")
    if not actuator_ok:
        print(f"    ❌ {env_name} unreachable — skipping remaining checks.")
        return {"env": env_name, "base_url": base_url, "overall_status": "FAILED", "error": "Service unreachable", "results": []}

    # ── Step 2: Fetch all tabs ──
    print(f"\n  [2] Fetch All Tabs  →  GET /subs-admin/api/v1/tabs")
    code, tabs_body, lat, err = api_get(base_url, "/subs-admin/api/v1/tabs")
    tabs_ok = code is not None and code < 500
    icon = "✅" if tabs_ok else "❌"
    print(f"    {icon} Status: {code}  |  Latency: {lat}ms")
    results.append({"name": "Fetch All Tabs", "status_code": code, "latency_ms": lat, "status": "PASS" if tabs_ok else "FAILED", "error": err})

    if err:
        print(f"       ⚠️  {err}")

    # Parse tabs to find tab IDs for tournament / gems / coins
    tab_map = {}  # tabType -> list of tab dicts
    if tabs_ok and isinstance(tabs_body, list):
        for tab in tabs_body:
            tt = (tab.get("tabType") or "").lower()
            tab_map.setdefault(tt, []).append(tab)
        print(f"    📋 Found {len(tabs_body)} tab(s): {list(tab_map.keys())}")
    elif tabs_ok and isinstance(tabs_body, dict) and "data" in tabs_body:
        for tab in tabs_body["data"]:
            tt = (tab.get("tabType") or "").lower()
            tab_map.setdefault(tt, []).append(tab)
        print(f"    📋 Found {len(tabs_body['data'])} tab(s): {list(tab_map.keys())}")

    # ── Step 3: Fetch all eligible passes and group by tabType ──
    print(f"\n  [3] Eligible Passes  →  GET /subs-admin/api/v1/eligible-passes")
    code, ebody, lat, err = api_get(base_url, "/subs-admin/api/v1/eligible-passes", params={"productId": "RUMMY", "userSegments": "1"})
    elig_ok = code == 200
    icon = "✅" if elig_ok else "❌"
    print(f"    {icon} Status: {code}  |  Latency: {lat}ms")
    results.append({"name": "Eligible Passes API", "status_code": code, "latency_ms": lat, "status": "PASS" if elig_ok else "FAILED", "error": err})

    if err:
        print(f"       ⚠️  {err}")
    if not elig_ok:
        print(f"    ❌ Cannot fetch passes — aborting pass checks.")
        return {"env": env_name, "base_url": base_url, "overall_status": "FAILED", "passed": "0/0", "results": results}

    # Group passes by tabType
    passes_by_type = {}  # tabType -> list of pass dicts
    if isinstance(ebody, list):
        for p in ebody:
            tt = (p.get("tabType") or "").lower()
            passes_by_type.setdefault(tt, []).append(p)
    print(f"    📋 Total passes: {len(ebody)}  |  Types: {sorted(passes_by_type.keys())}")

    # ── Step 4: Validate each target pass type ──
    print(f"\n  [4] Subscription Pass Checks")
    print(f"    {'PASS TYPE':<14} | {'TAB FOUND':<10} | {'TAB ID':<8} | {'# PASSES':<10} | {'PASS NAMES'}")
    print("    " + "-" * 76)

    for pt in TARGET_PASS_TYPES:
        tab_found = pt in tab_map
        tab_id = tab_map[pt][0].get("tabId") if tab_found else None
        passes = passes_by_type.get(pt, [])
        pass_count = len(passes)

        has_passes = pass_count > 0
        tab_icon = "✅" if tab_found else "❌"
        pass_icon = "✅" if has_passes else "❌"
        tid_str = str(tab_id) if tab_id is not None else "—"
        pass_names = ", ".join(p.get("name", "?") for p in passes) if passes else "None"

        status = "PASS" if (tab_found and has_passes) else "FAILED"
        print(f"    {tab_icon} {pt.capitalize():<12} | {'Yes' if tab_found else 'No':<10} | {tid_str:<8} | {pass_icon} {pass_count:<8} | {pass_names}")

        results.append({
            "name": f"{pt.capitalize()} Passes",
            "tab_id": tab_id,
            "pass_count": pass_count,
            "passes": [{"passId": p.get("passId"), "name": p.get("name")} for p in passes],
            "status": status,
        })

    # ── Step 5: Verify individual pass fetch (spot-check one pass per type) ──
    print(f"\n  [5] Spot-Check: Fetch Individual Pass by passId")
    for pt in TARGET_PASS_TYPES:
        passes = passes_by_type.get(pt, [])
        if not passes:
            continue
        sample = passes[0]
        pid = sample.get("passId")
        pcode, pbody, plat, perr = api_get(base_url, f"/subs-admin/api/v1/pass/{pid}")
        ok = pcode == 200
        icon = "✅" if ok else "❌"
        print(f"    {icon} {pt.capitalize():<12} passId={pid}  [{pcode}]  {plat}ms")
        results.append({
            "name": f"{pt.capitalize()} Pass Fetch (passId={pid})",
            "status_code": pcode,
            "latency_ms": plat,
            "status": "PASS" if ok else "FAILED",
            "error": perr,
        })

    # ── Summary ──
    passed = sum(1 for r in results if r["status"] == "PASS")
    total = len(results)
    overall = "PASS" if passed == total else "FAILED"

    summary = {
        "env": env_name,
        "base_url": base_url,
        "overall_status": overall,
        "passed": f"{passed}/{total}",
        "results": results,
    }

    print(f"\n  {'─' * 50}")
    print(f"  [{env_name}] Result: {overall}  ({passed}/{total} checks passed)")
    return summary


def run_tc6(env_name=None, env_config=None):
    # Single-env mode (called from run_all.py)
    if env_name and env_config:
        return check_environment(env_name, env_config)

    # Multi-env standalone mode
    envs = load_json('environments.json')
    print("\n" + "#" * 70)
    print("  TC6: Subscription Admin API — Multi-Environment Health Check")
    print(f"  Environments: {', '.join(envs.keys())}")
    print("#" * 70)

    all_summaries = []
    for ename, econfig in envs.items():
        summary = check_environment(ename, econfig)
        all_summaries.append(summary)

    # ── Final Cross-Environment Report ──
    print(f"\n\n{'#' * 70}")
    print("  FINAL REPORT — All Environments")
    print(f"{'#' * 70}")
    print(f"\n  {'ENVIRONMENT':<8} | {'STATUS':<8} | {'CHECKS':<10} | {'URL'}")
    print("  " + "-" * 65)

    all_pass = True
    for s in all_summaries:
        env = s.get("env", "?")
        status = s.get("overall_status", "FAILED")
        checks = s.get("passed", "0/0")
        url = s.get("base_url", "")
        icon = "✅" if status == "PASS" else "❌"
        print(f"  {icon} {env:<6} | {status:<8} | {checks:<10} | {url}")
        if status != "PASS":
            all_pass = False

    grand_status = "PASS" if all_pass else "FAILED"
    print(f"\n  Grand Total: {grand_status}")
    print(f"{'#' * 70}")

    print("\n" + json.dumps(all_summaries, indent=2))
    return all_summaries


if __name__ == "__main__":
    run_tc6()
