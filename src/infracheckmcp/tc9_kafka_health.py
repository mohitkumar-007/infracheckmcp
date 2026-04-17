import socket
import struct
import time
import json
import os


def load_json(filename):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    with open(file_path, 'r') as f:
        return json.load(f)


def _build_api_versions_request():
    """Build a Kafka ApiVersions (key=18) v0 request — the simplest
    Kafka wire-protocol message. Every broker supports it without auth."""
    api_key = 18        # ApiVersions
    api_version = 0
    correlation_id = 1
    client_id = b"infra-health-check"

    # Header: api_key(2) + api_version(2) + correlation_id(4) + client_id_len(2) + client_id
    header = struct.pack(">hhih",
                         api_key, api_version, correlation_id, len(client_id))
    header += client_id

    # Frame: size(4) + header
    frame = struct.pack(">i", len(header)) + header
    return frame, correlation_id


def check_broker(ip, port):
    """Check a single Kafka broker: TCP reachability + protocol handshake."""
    result = {
        "broker": f"{ip}:{port}",
        "tcp_reachable": False,
        "kafka_responsive": False,
        "latency_ms": None,
        "error": None,
    }

    # Step 1: TCP socket check
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        start = time.perf_counter()
        sock.connect((ip, port))
        result["tcp_reachable"] = True
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        result["error"] = f"TCP connect failed: {e}"
        return result

    # Step 2: Kafka ApiVersions handshake
    try:
        req, corr_id = _build_api_versions_request()
        sock.sendall(req)

        # Read 4-byte response length
        resp_len_bytes = _recv_exact(sock, 4)
        resp_len = struct.unpack(">i", resp_len_bytes)[0]

        # Read response body (at least correlation_id)
        resp_body = _recv_exact(sock, min(resp_len, 4096))
        latency = round((time.perf_counter() - start) * 1000)
        result["latency_ms"] = latency

        resp_corr_id = struct.unpack(">i", resp_body[:4])[0]
        if resp_corr_id == corr_id:
            result["kafka_responsive"] = True
        else:
            result["error"] = f"Unexpected correlation ID: {resp_corr_id}"
    except Exception as e:
        result["error"] = f"Kafka handshake failed: {e}"
    finally:
        sock.close()

    return result


def _recv_exact(sock, n):
    """Receive exactly n bytes from the socket."""
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection closed while reading")
        data += chunk
    return data


def run_tc9(env_name, env_config):
    brokers = env_config.get("kafka_brokers", [])
    if not brokers:
        print(f"  ⚠️  No kafka_brokers configured for {env_name} — skipping TC9.")
        return {"env": env_name, "test": "TC9", "status": "SKIPPED", "broker_health": []}

    print(f"\n{'=' * 70}")
    print(f"  [{env_name}] Kafka Broker — Health Check")
    print(f"{'=' * 70}")
    print(f"\n  {'BROKER':<25} | {'TCP':<6} | {'KAFKA':<6} | {'LATENCY':<10}")
    print("  " + "-" * 55)

    broker_results = []
    for entry in brokers:
        ip, port = entry["ip"], entry["port"]
        r = check_broker(ip, port)
        broker_results.append(r)

        tcp_icon = "✅" if r["tcp_reachable"] else "❌"
        kafka_icon = "✅" if r["kafka_responsive"] else "❌"
        latency = f"{r['latency_ms']}ms" if r["latency_ms"] is not None else "N/A"
        print(f"  {r['broker']:<25} | {tcp_icon:<6} | {kafka_icon:<6} | {latency:<10}")
        if r["error"]:
            print(f"    ⚠️  {r['error']}")

    passed = sum(1 for r in broker_results if r["kafka_responsive"])
    total = len(broker_results)
    status = "PASS" if passed == total else "FAILED"

    print(f"\n  ──────────────────────────────────────────────────")
    print(f"  [{env_name}] Result: {status}  ({passed}/{total} brokers healthy)")

    return {
        "env": env_name,
        "test": "TC9",
        "status": status,
        "summary": f"{passed}/{total} Kafka brokers healthy",
        "broker_health": broker_results,
    }


if __name__ == "__main__":
    envs = load_json('environments.json')
    for env_name, env_config in envs.items():
        result = run_tc9(env_name, env_config)
        print(json.dumps(result, indent=2))
