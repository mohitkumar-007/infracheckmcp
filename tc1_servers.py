import socket
import requests
import json
import os

def load_json(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as f:
        return json.load(f)

def check_server_health(name, config):
    ip = config["ip"]
    port = config["port"]
    path = config.get("path", "/")
    server_type = config.get("type", "http") # Default to http if not specified
    
    result = {
        "server_name": name,
        "ip": ip,
        "port": port,
        "available": False,  
        "active": False,     
        "status_code": None
    }

    # 1. Check Availability (TCP Socket) - ALL servers must pass this
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(2) 
            s.connect((ip, port))
            result["available"] = True
    except (socket.timeout, ConnectionRefusedError):
        return result 

    # 2. For tcp/game servers: port open on dedicated port = active
    if server_type == "tcp":
        result["active"] = True
        return result

    # 3. For http/backend servers: HTTP request to verify service responds
    try:
        url = f"http://{ip}:{port}{path}"
        response = requests.get(url, timeout=3)
        result["status_code"] = response.status_code
        if response.status_code < 500:
            result["active"] = True
    except requests.exceptions.RequestException as e:
        result["error_details"] = str(e)

    return result

def run_tc1(env_name, env_config):
    servers = env_config.get("servers", {})
    if not servers:
        print(f"  ⚠️  No servers configured for {env_name} — skipping TC1.")
        return {"env": env_name, "test": "TC1", "status": "SKIPPED", "server_health": []}

    tc1_results = {"env": env_name, "test": "TC1", "server_health": []}
    
    for name, config in servers.items():
        tc1_results["server_health"].append(check_server_health(name, config))

    passed = sum(1 for s in tc1_results["server_health"] if s["active"])
    total = len(tc1_results["server_health"])
    tc1_results["status"] = "PASS" if passed == total else "FAILED"
    tc1_results["summary"] = f"{passed}/{total} servers active"
    return tc1_results

if __name__ == "__main__":
    envs = load_json('environments.json')
    for env_name, env_config in envs.items():
        print(f"\n{'=' * 60}")
        print(f"  TC1: Server Health — [{env_name}]")
        print(f"{'=' * 60}")
        result = run_tc1(env_name, env_config)
        print(json.dumps(result, indent=2))