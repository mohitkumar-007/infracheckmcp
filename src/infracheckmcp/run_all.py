import asyncio
import json
import os
import time

from infracheckmcp.tc1_servers import run_tc1
from infracheckmcp.tc2_websocket import run_tc2
from infracheckmcp.tc3_availableserverlist import run_tc3
from infracheckmcp.tc4_e2e_game_flow import run_tc4
from infracheckmcp.tc5_wslogincheck import run_tc5
from infracheckmcp.tc6_subscription_api import run_tc6
from infracheckmcp.tc7_kyc_health import run_tc7
from infracheckmcp.tc8_dms_health import run_tc8


def load_json(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as f:
        return json.load(f)


def print_banner(env_name):
    print(f"\n{'#' * 70}")
    print(f"  ENVIRONMENT: {env_name}")
    print(f"{'#' * 70}")


def print_tc_header(tc_name):
    print(f"\n  {'─' * 60}")
    print(f"  {tc_name}")
    print(f"  {'─' * 60}")


def run_all():
    envs = load_json('environments.json')
    start_time = time.perf_counter()

    all_results = {}  # env_name -> list of tc results

    for env_name, env_config in envs.items():
        print_banner(env_name)
        env_results = []

        # TC1: Server Health
        print_tc_header("TC1: Server Health Check")
        tc1 = run_tc1(env_name, env_config)
        env_results.append(tc1)
        icon = "✅" if tc1["status"] == "PASS" else ("⏭️" if tc1["status"] == "SKIPPED" else "❌")
        print(f"    {icon} TC1: {tc1['status']}  —  {tc1.get('summary', '')}")

        # TC2: WebSocket Health
        print_tc_header("TC2: WebSocket Health Check")
        tc2 = asyncio.run(run_tc2(env_name, env_config))
        env_results.append(tc2)
        icon = "✅" if tc2["status"] == "PASS" else ("⏭️" if tc2["status"] == "SKIPPED" else "❌")
        print(f"    {icon} TC2: {tc2['status']}  —  {tc2.get('summary', '')}")

        # TC3: Server Inventory
        print_tc_header("TC3: Server Inventory Check")
        tc3 = run_tc3(env_name, env_config)
        env_results.append(tc3)
        icon = "✅" if tc3["status"] == "PASS" else ("⏭️" if tc3["status"] == "SKIPPED" else "❌")
        print(f"    {icon} TC3: {tc3['status']}  —  {tc3.get('summary', '')}")

        # TC4: Game Protocol Health
        print_tc_header("TC4: Game Protocol Health Check")
        tc4 = asyncio.run(run_tc4(env_name, env_config))
        env_results.append(tc4)
        icon = "✅" if tc4["status"] == "PASS" else ("⏭️" if tc4["status"] == "SKIPPED" else "❌")
        print(f"    {icon} TC4: {tc4['status']}  —  {tc4.get('summary', '')}")

        # TC5: WS Login
        print_tc_header("TC5: WS Login Check")
        tc5 = asyncio.run(run_tc5(env_name, env_config))
        env_results.append(tc5)
        icon = "✅" if tc5["status"] == "PASS" else ("⏭️" if tc5["status"] == "SKIPPED" else "❌")
        user_id = tc5.get("data", {}).get("userId", "N/A")
        print(f"    {icon} TC5: {tc5['status']}  —  userId: {user_id}")

        # TC6: Subscription API
        print_tc_header("TC6: Subscription API Health Check")
        tc6 = run_tc6(env_name, env_config)
        env_results.append(tc6)
        tc6_status = tc6.get("overall_status", tc6.get("status", "FAILED"))
        icon = "✅" if tc6_status == "PASS" else ("⏭️" if tc6_status == "SKIPPED" else "❌")
        print(f"    {icon} TC6: {tc6_status}  —  {tc6.get('passed', '')}")

        # TC7: KYC Service Health
        print_tc_header("TC7: KYC Service Health Check")
        tc7 = run_tc7(env_name, env_config)
        env_results.append(tc7)
        icon = "✅" if tc7["status"] == "PASS" else ("⏭️" if tc7["status"] == "SKIPPED" else "❌")
        print(f"    {icon} TC7: {tc7['status']}  —  {tc7.get('passed', '')}")

        # TC8: DMS Service Health
        print_tc_header("TC8: DMS Service Health Check")
        tc8 = run_tc8(env_name, env_config)
        env_results.append(tc8)
        icon = "✅" if tc8["status"] == "PASS" else ("⏭️" if tc8["status"] == "SKIPPED" else "❌")
        print(f"    {icon} TC8: {tc8['status']}  —  {tc8.get('passed', '')}")

        all_results[env_name] = env_results

    # ── Grand Summary ──
    elapsed = round(time.perf_counter() - start_time, 1)
    print(f"\n\n{'#' * 70}")
    print(f"  GRAND SUMMARY  —  All Environments × All Test Cases")
    print(f"  Total Time: {elapsed}s")
    print(f"{'#' * 70}")

    tc_labels = ["TC1", "TC2", "TC3", "TC4", "TC5", "TC6", "TC7", "TC8"]
    header = f"  {'ENV':<8}" + "".join(f" | {t:<8}" for t in tc_labels) + " | OVERALL"
    print(f"\n{header}")
    print("  " + "-" * (10 + 11 * len(tc_labels) + 10))

    grand_pass = True
    for env_name, results in all_results.items():
        row = f"  {env_name:<8}"
        env_pass = True
        for r in results:
            s = r.get("overall_status", r.get("status", "FAILED"))
            if s == "PASS":
                row += f" | {'✅ PASS':<8}"
            elif s == "SKIPPED":
                row += f" | {'⏭️ SKIP':<8}"
            else:
                row += f" | {'❌ FAIL':<8}"
                env_pass = False
        overall = "✅ PASS" if env_pass else "❌ FAIL"
        row += f" | {overall}"
        print(row)
        if not env_pass:
            grand_pass = False

    grand = "PASS" if grand_pass else "FAILED"
    print(f"\n  Grand Total: {grand}")
    print(f"{'#' * 70}\n")


if __name__ == "__main__":
    run_all()
