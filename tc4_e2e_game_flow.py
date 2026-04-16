import asyncio
import websockets
import json
import time
import os

def load_json(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as f:
        return json.load(f)

async def check_protocol_health(server, ws_gateway):
    url = f"{ws_gateway}/{server['ip']}"
    
    result = {
        "server_name": server['name'],
        "ip": server['ip'],
        "status": "FAILED",
        "steps": {"ws_connect": "PENDING", "handshake": "PENDING"},
        "latency_ms": 0,
        "error": None
    }
    
    start_time = time.perf_counter()
    
    try:
        async with websockets.connect(url, open_timeout=5) as websocket:
            result["steps"]["ws_connect"] = "SUCCESS"
            
            init_payload = json.dumps({
                "_id": "SM_INIT", 
                "f1": int(time.time() * 1000)
            })
            
            await websocket.send(init_payload)
            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
            
            if "SM_INIT" in response:
                result["steps"]["handshake"] = "SUCCESS"
                result["status"] = "PASS"
            
            result["latency_ms"] = round((time.perf_counter() - start_time) * 1000)
            
    except Exception as e:
        result["error"] = str(e)
    
    return result

async def run_tc4(env_name, env_config):
    servers = env_config.get("servers", {})
    ws_gateway = env_config.get("ws_gateway", "")

    # Build target list from tcp servers in config
    target_servers = [
        {"name": name, "ip": cfg["ip"]}
        for name, cfg in servers.items()
        if cfg.get("type") == "tcp"
    ]

    if not target_servers or not ws_gateway:
        print(f"  ⚠️  No TCP servers/gateway for {env_name} — skipping TC4.")
        return {"env": env_name, "test": "TC4", "status": "SKIPPED", "results": []}

    print(f"  {'SERVER':<20} | {'CONNECT':<10} | {'HANDSHAKE':<10} | {'LATENCY':<10}")
    print("  " + "-" * 56)
    
    tasks = [check_protocol_health(s, ws_gateway) for s in target_servers]
    reports = await asyncio.gather(*tasks)
    
    for r in reports:
        connect = "✅" if r["steps"]["ws_connect"] == "SUCCESS" else "❌"
        handshake = "✅" if r["steps"]["handshake"] == "SUCCESS" else "❌"
        latency = f"{r['latency_ms']}ms" if r['status'] == "PASS" else "N/A"
        print(f"  {r['server_name']:<20} | {connect:<10} | {handshake:<10} | {latency:<10}")

    passed = sum(1 for r in reports if r["status"] == "PASS")
    total = len(reports)
    status = "PASS" if passed == total else "FAILED"
    return {"env": env_name, "test": "TC4", "status": status, "summary": f"{passed}/{total} protocols OK", "results": reports}

if __name__ == "__main__":
    envs = load_json('environments.json')
    for env_name, env_config in envs.items():
        print(f"\n{'=' * 60}")
        print(f"  TC4: Game Protocol Health — [{env_name}]")
        print(f"{'=' * 60}")
        result = asyncio.run(run_tc4(env_name, env_config))
        print(json.dumps({"env": result["env"], "status": result["status"], "summary": result.get("summary", "")}, indent=2))