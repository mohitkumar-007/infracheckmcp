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

async def tcp_server_health_check(server_name, ip, ws_gateway):
    # Constructing the secure gateway URL dynamically
    url = f"{ws_gateway}/{ip}"
    
    result = {
        "server_name": server_name,
        "url": url,
        "status": "FAILED",
        "latency_ms": None,
        "error": None
    }
    
    try:
        async with websockets.connect(url, open_timeout=5) as websocket:
            ping_payload = json.dumps({"type": "ping"})
            
            start_time = time.time()
            await websocket.send(ping_payload)
            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
            end_time = time.time()
            
            latency = round((end_time - start_time) * 1000) 
            
            result["status"] = "SUCCESS"
            result["latency_ms"] = latency
            result["response_received"] = response
            
    except asyncio.TimeoutError:
        result["error"] = "Connected successfully, but server timed out waiting for a pong reply."
    except Exception as e:
        result["error"] = str(e)

    return result

async def run_tc2(env_name, env_config):
    servers = env_config.get("servers", {})
    ws_gateway = env_config.get("ws_gateway", "")
    
    if not servers or not ws_gateway:
        print(f"  ⚠️  No servers/gateway configured for {env_name} — skipping TC2.")
        return {"env": env_name, "test": "TC2", "status": "SKIPPED", "websocket_health": []}

    final_results = {"env": env_name, "test": "TC2", "websocket_health": []}
    
    for name, config in servers.items():
        server_type = config.get("type", "http")
        
        if server_type == "tcp":
            print(f"  Testing {name} at {config['ip']}...")
            result = await tcp_server_health_check(name, config["ip"], ws_gateway)
            final_results["websocket_health"].append(result)

    passed = sum(1 for s in final_results["websocket_health"] if s["status"] == "SUCCESS")
    total = len(final_results["websocket_health"])
    final_results["status"] = "PASS" if total > 0 and passed == total else ("SKIPPED" if total == 0 else "FAILED")
    final_results["summary"] = f"{passed}/{total} WS connections OK"
    return final_results

if __name__ == "__main__":
    envs = load_json('environments.json')
    for env_name, env_config in envs.items():
        print(f"\n{'=' * 60}")
        print(f"  TC2: WebSocket Health — [{env_name}]")
        print(f"{'=' * 60}")
        result = asyncio.run(run_tc2(env_name, env_config))
        print(json.dumps(result, indent=2))