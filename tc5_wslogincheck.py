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

async def test_central_login(auth_url, login_creds):
    login_payload = {
        "type": "cm-login-pass",
        "network": "JUNGLEERUMMY",
        "login": login_creds["phone"],
        "password": login_creds["password"],
        "extras": {
            "deviceName": "QA-Automation",
            "osName": "Linux",
            "browserName": "Python-Harness"
        }
    }

    result = {
        "test": "Central Authentication Flow",
        "url": auth_url,
        "status": "FAILED",
        "data": {}
    }

    try:
        async with websockets.connect(auth_url, open_timeout=10) as ws:
            
            # 1. Handshake
            await ws.send(json.dumps({"_id": "SM_INIT", "f1": int(time.time() * 1000)}))
            await asyncio.wait_for(ws.recv(), timeout=3)
            
            # 2. Send Login
            await ws.send(json.dumps(login_payload))

            # 3. Listen until we find the Login response
            print(f"    👂 Listening for Auth Response...")
            start_listen_time = time.time()
            msg_count = 0
            received_types = []
            
            POST_AUTH_INDICATORS = {
                "sm-lobby-config", "sm-lobby-config-v2", "sm-game-init-config",
                "sm-game-client-properties", "sm-multi-table-config"
            }
            
            while time.time() - start_listen_time < 15:
                try:
                    response = await asyncio.wait_for(ws.recv(), timeout=2.0)
                    resp_data = json.loads(response)
                    msg_type = resp_data.get("type")
                    msg_count += 1
                    
                    if msg_type:
                        received_types.append(msg_type)
                    
                    if msg_type == "sm-login-success":
                        result["status"] = "PASS"
                        result["data"] = {
                            "userId": resp_data.get("userId"),
                            "authToken": bool(resp_data.get("authToken")),
                            "gsAuthToken": bool(resp_data.get("gsAuthToken")),
                            "apiAccessToken": bool(resp_data.get("apiAccessToken")),
                            "login_method": "explicit_success"
                        }
                        return result
                    
                    elif msg_type == "sm-login-fail":
                        result["error"] = f"Login Failed: {resp_data.get('reason')}"
                        return result
                        
                except asyncio.TimeoutError:
                    break
            
            auth_signals = POST_AUTH_INDICATORS.intersection(received_types)
            if auth_signals:
                result["status"] = "PASS"
                result["data"] = {
                    "messages_received": msg_count,
                    "login_method": "implicit (post-auth configs detected)",
                    "auth_signals": list(auth_signals)
                }
            else:
                result["error"] = "Timed out waiting for login response."

    except Exception as e:
        result["error"] = str(e)

    return result

async def run_tc5(env_name, env_config):
    auth_url = env_config.get("auth_url", "")
    login_creds = env_config.get("login", {})

    if not auth_url or not login_creds:
        print(f"  ⚠️  No auth_url/login for {env_name} — skipping TC5.")
        return {"env": env_name, "test": "TC5", "status": "SKIPPED"}

    result = await test_central_login(auth_url, login_creds)
    result["env"] = env_name
    result["test"] = "TC5"
    user_id = result.get("data", {}).get("userId", "N/A")
    icon = "✅" if result["status"] == "PASS" else "❌"
    print(f"    {icon} Login: {result['status']}  |  userId: {user_id}")
    if result.get("error"):
        print(f"       ⚠️  {result['error']}")
    return result

if __name__ == "__main__":
    envs = load_json('environments.json')
    for env_name, env_config in envs.items():
        print(f"\n{'=' * 60}")
        print(f"  TC5: WS Login Check — [{env_name}]")
        print(f"{'=' * 60}")
        result = asyncio.run(run_tc5(env_name, env_config))
        print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(run_tc5())