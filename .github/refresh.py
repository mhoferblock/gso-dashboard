#!/usr/bin/env python3
"""
GSO Dashboard Refresh Script
Pulls data from Looker dashboard 39532 via MCP blockdata server,
saves raw data, and uploads to Blockcell.

Usage: python3 refresh.py
"""

import json
import subprocess
import sys
import os
import time
import select

WORKSPACE = os.environ.get("GITHUB_WORKSPACE", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UVX_WRAPPER = "/Users/mhofer/.config/goose/bin/uvx-wrapper"
DASHBOARD_ID = "39532"
FILTERS = {
    "Completed Date": "90 day",
    "Created Date": "365 day",
    "Seller Country": "US,CA,GB,JP,ES,FR,AU,IE"
}


class MCPClient:
    """Simple MCP client that communicates with an MCP server via stdio."""
    
    def __init__(self, cmd, args, startup_wait=8):
        env = {**os.environ, "GOOSE_UV_REGISTRY": "https://global.block-artifacts.com/artifactory/api/pypi/block-pypi/simple/"}
        self.proc = subprocess.Popen(
            [cmd] + args,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, env=env, bufsize=0
        )
        time.sleep(startup_wait)
        self._msg_id = 0
        self._initialize()
    
    def _next_id(self):
        self._msg_id += 1
        return self._msg_id
    
    def _send(self, msg):
        data = json.dumps(msg) + "\n"
        self.proc.stdin.write(data)
        self.proc.stdin.flush()
    
    def _recv(self, timeout=180):
        end_time = time.time() + timeout
        while time.time() < end_time:
            ready, _, _ = select.select([self.proc.stdout], [], [], 5)
            if ready:
                line = self.proc.stdout.readline().strip()
                if line:
                    try:
                        return json.loads(line)
                    except json.JSONDecodeError:
                        continue
        return None
    
    def _initialize(self):
        msg_id = self._next_id()
        self._send({
            "jsonrpc": "2.0", "id": msg_id, "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "gso-refresh", "version": "1.0.0"}
            }
        })
        resp = self._recv(30)
        if not resp or resp.get("id") != msg_id:
            raise RuntimeError(f"MCP initialize failed: {resp}")
        
        # Send initialized notification
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
        time.sleep(1)
        print("  ✓ MCP server initialized")
    
    def call_tool(self, name, arguments, timeout=180):
        msg_id = self._next_id()
        self._send({
            "jsonrpc": "2.0", "id": msg_id, "method": "tools/call",
            "params": {"name": name, "arguments": arguments}
        })
        
        # Read responses until we get the one matching our ID
        end_time = time.time() + timeout
        while time.time() < end_time:
            resp = self._recv(timeout=min(30, end_time - time.time()))
            if resp is None:
                continue
            if resp.get("id") == msg_id:
                if "result" in resp:
                    return self._extract_text(resp["result"])
                elif "error" in resp:
                    print(f"  ✗ Tool error: {resp['error']}", file=sys.stderr)
                    return None
            # Skip notifications/other messages
        
        print(f"  ✗ Timeout waiting for tool response", file=sys.stderr)
        return None
    
    def _extract_text(self, result):
        """Extract text content from MCP tool result."""
        if isinstance(result, dict) and "content" in result:
            texts = []
            for item in result["content"]:
                if isinstance(item, dict) and item.get("type") == "text":
                    texts.append(item["text"])
            return "\n".join(texts) if texts else str(result)
        return str(result)
    
    def close(self):
        try:
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except:
            self.proc.kill()


def pull_looker_data():
    """Pull all data from Looker dashboard 39532."""
    print("📊 Starting Blockdata MCP server...")
    client = MCPClient(UVX_WRAPPER, ["mcp_block_data@latest"])
    
    try:
        # Step 1: Get dashboard metadata
        print("📊 Getting dashboard metadata...")
        meta = client.call_tool("run_dashboard", {
            "dashboard_id": DASHBOARD_ID,
            "platform": "looker"
        })
        
        if not meta:
            print("❌ Failed to get dashboard metadata", file=sys.stderr)
            return None
        
        print(f"  ✓ Metadata received ({len(meta)} chars)")
        
        # Parse query IDs from metadata (alphanumeric hash IDs)
        import re
        query_ids = list(set(re.findall(r'"query_id":"([^"]+)"', meta)))
        
        if not query_ids:
            # Try alternative patterns
            query_ids = list(set(re.findall(r'query_id["\s:]+([A-Za-z0-9]+)', meta)))
        
        if not query_ids:
            print("❌ No query IDs found in metadata", file=sys.stderr)
            print(f"  Preview: {meta[:500]}", file=sys.stderr)
            return None
        
        print(f"  ✓ Found {len(query_ids)} queries: {query_ids}")
        
        # Step 2: Pull data — all queries at once
        all_results = {"metadata": meta, "queries": {}, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S %Z")}
        
        print(f"📊 Pulling all {len(query_ids)} queries at once...")
        result = client.call_tool("run_dashboard", {
            "dashboard_id": DASHBOARD_ID,
            "platform": "looker",
            "query_ids": query_ids,
            "filters": FILTERS
        }, timeout=300)
        
        if result:
            all_results["queries"]["all"] = result
            print(f"  ✓ All data received ({len(result)} chars)")
        else:
            print(f"  ✗ Query failed, trying in smaller batches...")
            batch_size = 5
            for i in range(0, len(query_ids), batch_size):
                batch = query_ids[i:i+batch_size]
                print(f"📊 Pulling batch {i//batch_size + 1}: queries {[q[:8] for q in batch]}...")
                
                batch_result = client.call_tool("run_dashboard", {
                    "dashboard_id": DASHBOARD_ID,
                    "platform": "looker",
                    "query_ids": batch,
                    "filters": FILTERS
                }, timeout=180)
                
                if batch_result:
                    all_results["queries"][f"batch_{i//batch_size}"] = batch_result
                    print(f"  ✓ Batch received ({len(batch_result)} chars)")
                else:
                    print(f"  ✗ Batch failed")
                
                time.sleep(2)
        
        return all_results
    
    finally:
        client.close()


def upload_to_blockcell():
    """Upload the dashboard to Blockcell."""
    print("🚀 Starting Blockcell MCP server...")
    client = MCPClient(UVX_WRAPPER, ["mcp_blockcell@latest"])
    
    try:
        print("🚀 Uploading to Blockcell...")
        result = client.call_tool("manage_site", {
            "site_name": "gso-dashboard",
            "action": "upload",
            "directory_path": WORKSPACE
        }, timeout=60)
        
        if result:
            print(f"  ✓ Upload complete")
            return True
        else:
            print("  ✗ Upload failed", file=sys.stderr)
            return False
    finally:
        client.close()


def main():
    print(f"{'='*60}")
    print(f"🔄 GSO Dashboard Refresh")
    print(f"   Time: {time.strftime('%Y-%m-%d %I:%M %p %Z')}")
    print(f"   Workspace: {WORKSPACE}")
    print(f"{'='*60}")
    
    # Step 1: Pull fresh data from Looker
    data = pull_looker_data()
    
    if data:
        # Save raw data for reference and for goose to use
        data_path = os.path.join(WORKSPACE, ".github", "latest-data.json")
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        with open(data_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Saved raw data to {data_path}")
        print(f"   Total data size: {os.path.getsize(data_path):,} bytes")
    else:
        print("⚠️  Could not pull fresh data from Looker")
        print("   Dashboard will remain unchanged")
    
    # Step 2: Upload to Blockcell (even if data didn't change, ensures site is live)
    upload_to_blockcell()
    
    print(f"\n{'='*60}")
    print(f"✅ Refresh complete at {time.strftime('%Y-%m-%d %I:%M %p %Z')}")
    print(f"   Dashboard: https://blockcell.sqprod.co/sites/gso-dashboard/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
