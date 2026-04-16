import json
import os

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
        return {"env": env_name, "test": "TC3", "status": "SKIPPED", "missing_roles": [], "found_roles": []}

    scanned_names = list(servers.keys())
    
    result = {
        "env": env_name,
        "test": "TC3",
        "test_name": "Inventory Validation",
        "status": "PASS",
        "missing_roles": [],
        "found_roles": []
    }
    
    for role in expected_roles:
        if any(role.lower() in name.lower() for name in scanned_names):
            result["found_roles"].append(role)
        else:
            result["missing_roles"].append(role)
            result["status"] = "FAILED"

    result["summary"] = f"{len(result['found_roles'])}/{len(expected_roles)} roles found"
    return result

if __name__ == "__main__":
    envs = load_json('environments.json')
    for env_name, env_config in envs.items():
        print(f"\n{'=' * 60}")
        print(f"  TC3: Inventory Check — [{env_name}]")
        print(f"{'=' * 60}")
        result = run_tc3(env_name, env_config)
        print(json.dumps(result, indent=2))