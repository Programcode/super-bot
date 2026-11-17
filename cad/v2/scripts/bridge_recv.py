# Tiny file bridge for Fusion scripts on Adam's Mac.
# GET /<name>  -> serves a file from SCRIPTS dir (flat names only)
# PUT /<name>  -> writes body to OUT dir (flat names only, or one subdir level like stl__x.stl)
import sys, os, http.server, re
OUT, SCRIPTS = sys.argv[1], sys.argv[2]
SAFE = re.compile(r'^[A-Za-z0-9._-]+$')
class H(http.server.BaseHTTPRequestHandler):
    def _name(self):
        n = self.path.lstrip('/')
        if not SAFE.match(n) or n.startswith('.'):
            self.send_error(400); return None
        return n
    def do_GET(self):
        n = self._name()
        if not n: return
        p = os.path.join(SCRIPTS, n)
        if not os.path.isfile(p):
            self.send_error(404); return
        d = open(p, 'rb').read()
        self.send_response(200); self.send_header('Content-Length', str(len(d))); self.end_headers(); self.wfile.write(d)
    def do_PUT(self):
        n = self._name()
        if not n: return
        ln = int(self.headers.get('Content-Length', 0))
        d = self.rfile.read(ln)
        os.makedirs(OUT, exist_ok=True)
        open(os.path.join(OUT, n), 'wb').write(d)
        self.send_response(200); self.send_header('Content-Length', '2'); self.end_headers(); self.wfile.write(b'ok')
    def log_message(self, *a): pass
http.server.ThreadingHTTPServer(('100.115.45.111', 8766), H).serve_forever()
