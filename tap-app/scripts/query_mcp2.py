"""Query NotebookLM MCP with correct format."""
import subprocess
import json

def send_request(request, timeout=30):
    proc = subprocess.Popen(
        ['uvx', '--from', 'notebooklm-mcp-cli', 'notebooklm-mcp'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    stdout, stderr = proc.communicate(input=json.dumps(request) + '\n', timeout=timeout)
    return stdout, stderr

# Initialize first
init_request = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "id": 1,
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "tap-research", "version": "1.0"}
    }
}

print("Initializing...")
stdout, stderr = send_request(init_request)
print(f"Init: {stdout[:300]}")

# Send initialized notification
notif = {
    "jsonrpc": "2.0",
    "method": "notifications/initialized",
    "params": {}
}
stdout, stderr = send_request(notif)
print(f"Notif: {stdout[:200]}")

# Now try tools/list with correct params format
tools_request = {
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 2,
    "params": {}
}

print("\nListing tools...")
stdout, stderr = send_request(tools_request)
print(f"Tools: {stdout[:3000]}")

# Parse and show tools
try:
    data = json.loads(stdout)
    if "result" in data:
        tools = data["result"].get("tools", [])
        print(f"\n=== AVAILABLE TOOLS ({len(tools)}) ===")
        for t in tools:
            print(f"\n  {t.get('name')}:")
            print(f"    Desc: {t.get('description', '')[:150]}")
            if 'inputSchema' in t:
                props = t['inputSchema'].get('properties', {})
                print(f"    Params: {list(props.keys())}")
    elif "error" in data:
        print(f"Error: {data['error']}")
except Exception as e:
    print(f"Parse error: {e}")
