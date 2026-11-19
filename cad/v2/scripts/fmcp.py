"""fmcp.py: call the Fusion MCP server over HTTP (JSON-RPC) when the session's MCP client is down.

usage:
  python3 fmcp.py read   '<json args>'          -> fusion_mcp_read
  python3 fmcp.py exec   <script.py> [ro]       -> fusion_mcp_execute featureType=script (ro = readOnly)
  python3 fmcp.py job    <tag> "<jobs list>"    -> runs the v2 loader with JOBS/TAG (saves on success)
Prints the tool's text result. Exit 1 on an error result. Timeouts are long; the loader also
uploads its log to the bridge, so a timeout here doesn't lose the result.
"""
import json, re, sys, urllib.request

URL = 'http://127.0.0.1:27182/mcp'
H = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}


def post(body, sid=None, timeout=60):
    h = dict(H)
    if sid:
        h['Mcp-Session-Id'] = sid
    r = urllib.request.urlopen(urllib.request.Request(URL, data=json.dumps(body).encode(), headers=h, method='POST'), timeout=timeout)
    raw = r.read().decode()
    sid = r.headers.get('Mcp-Session-Id') or sid
    if raw.startswith('event:') or raw.startswith('data:'):
        data = [l[5:].strip() for l in raw.splitlines() if l.startswith('data:')]
        raw = data[-1] if data else '{}'
    return (json.loads(raw) if raw.strip() else {}), sid


def session():
    res, sid = post({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                     'params': {'protocolVersion': '2025-03-26', 'capabilities': {}, 'clientInfo': {'name': 'sbv2-fmcp', 'version': '1'}}})
    post({'jsonrpc': '2.0', 'method': 'notifications/initialized'}, sid)
    return sid


def call(name, args, timeout=900):
    sid = session()
    res, _ = post({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/call', 'params': {'name': name, 'arguments': args}}, sid, timeout=timeout)
    if 'error' in res:
        print('RPC ERROR', json.dumps(res['error'])[:2000])
        return 1
    out = res.get('result', {})
    texts = [c.get('text', '') for c in out.get('content', []) if c.get('type') == 'text']
    print('\n'.join(texts)[:20000])
    return 1 if out.get('isError') else 0


def main():
    mode = sys.argv[1]
    if mode == 'read':
        sys.exit(call('fusion_mcp_read', json.loads(sys.argv[2])))
    if mode == 'exec':
        src = open(sys.argv[2]).read()
        obj = {'script': src}
        if len(sys.argv) > 3 and sys.argv[3] == 'ro':
            obj['readOnly'] = True
        sys.exit(call('fusion_mcp_execute', {'featureType': 'script', 'object': obj}))
    if mode == 'job':
        src = open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), 'loader.py')).read()
        src = re.sub(r'^JOBS = .*$', 'JOBS = ' + sys.argv[3], src, flags=re.M)
        src = re.sub(r'^TAG = .*$', 'TAG = %r' % sys.argv[2], src, flags=re.M)
        sys.exit(call('fusion_mcp_execute', {'featureType': 'script', 'object': {'script': src}}))


if __name__ == '__main__':
    main()
