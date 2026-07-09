#!/usr/bin/env python3
"""Quick test: verify MCP Server starts and lists tools."""
import subprocess, json, time, sys

proc = subprocess.Popen(
    ['python3', '/home/ubuntu/security-tools-server/server.py'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True
)

def send(data):
    line = json.dumps(data)
    proc.stdin.write(line + '\n')
    proc.stdin.flush()

# Initialize
send({"jsonrpc":"2.0","id":1,"method":"initialize",
      "params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}})

send({"jsonrpc":"2.0","method":"notifications/initialized"})

# List tools
send({"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})

time.sleep(3)
proc.stdin.close()

out = proc.stdout.read()
err = proc.stderr.read()
proc.terminate()

ok = False
for line in out.strip().split('\n'):
    if not line.strip():
        continue
    try:
        data = json.loads(line)
        if 'result' in data and 'tools' in data.get('result', {}):
            tools = data['result']['tools']
            print(f'✅ Total tools listed: {len(tools)}')
            for t in tools:
                name = t.get('name','')
                marker = '🎯' if name in ('contract_audit','centralized_audit','production_audit') else '  '
                print(f'  {marker} {name}: {t.get("description","")[:80]}')
            ok = True
    except:
        pass

if not ok:
    print(f'❌ FAILED')
    print(f'STDOUT: {out[:1000]}')
    print(f'STDERR: {err[:500]}')
    sys.exit(1)
