"""Query NotebookLM MCP server."""
import subprocess
import json
import sys

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

# Step 1: Initialize
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

print("Initializing MCP server...")
stdout, stderr = send_request(init_request)
print(f"Init response: {stdout[:500]}")

# Step 2: List tools
tools_request = {
    "jsonrpc": "2.0",
    "method": "tools/list",
    "id": 2
}

print("\nListing tools...")
stdout, stderr = send_request(tools_request)
print(f"Tools response: {stdout[:2000]}")

# Parse tools
try:
    tools_data = json.loads(stdout)
    if "result" in tools_data:
        tools = tools_data["result"].get("tools", [])
        print(f"\nAvailable tools: {len(tools)}")
        for tool in tools:
            print(f"  - {tool.get('name')}: {tool.get('description', '')[:100]}")
except:
    pass
