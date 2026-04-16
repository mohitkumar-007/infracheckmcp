import json
import os

from infracheckmcp.tc1_servers import check_server_health

def load_json(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as f:
        return json.load(f)

def run_tc3(env_name, env_config):
    servers = env_config.get("servers", {})
    expected_roles = env_config.get("expected_servers", [])

    if not servers or not expected_roles:
        print(f"  ⚠️  No servers/expected list for {env_name} — skipping TC3.")
        return {"env": env_name, "test": "TC3", "status": "SKIPPED", "missing_roles": [], "found_roles": [], "unreachable": []}

    scanned_names = list(servers.keys())
    
    result = {
        "env": env_name,
        "test": "TC3",
        "test_name": "Inventory Validation",
        "status": "PASS",
        "missing_roles": [],
        "found_roles": [],
        "unreachable": []
    }
    
    for role in expected_roles:
        matched_name = next((name for name in scanned_names if role.lower() in name.lower()), None)
        if matched_name:
            cfg = servers[matched_name]
            health = check_server_health(matched_name, cfg)
            if health["active"]:
                result["found_roles"].append(role)
            else:
                result["unreachable"].append(role)
                result["status"] = "FAILED"
                print(f"    ❌ {role} — configured but NOT active ({cfg['ip']}:{cfg['port']})")
        else:
            result["missing_roles"].append(role)
            result["status"] = "FAILED"
            print(f"    ❌ {role} — not found in config")

    found = len(result["found_roles"])
    total = len(expected_roles)
    parts = [f"{found}/{total} roles active"]
    if result["unreachable"]:
        parts.append(f"{len(result['unreachable'])} unreachable: {', '.join(result['unreachable'])}")
    if result["missing_roles"]:
        parts.append(f"{len(result['missing_roles'])} missing: {', '.join(result['missing_roles'])}")
    result["summary"] = " | ".join(parts)
    return result

if __name__ == "__main__":
    envs = load_json('environments.json')
    for env_name, env_config in envs.items():
        print(f"\n{'=' * 60}")
        print(f"  TC3: Inventory Check — [{env_name}]")
        print(f"{'=' * 60}")
        result = run_tc3(env_name, env_config)
        print(json.dumps(result, indent=2))