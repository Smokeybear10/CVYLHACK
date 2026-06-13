import http.server, socketserver, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from aps.auth import get_token

class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/token":
            tok = get_token("data:read")
            body = json.dumps({"access_token": tok, "expires_in": 3600}).encode()
            self.send_response(200); self.send_header("Content-Type", "application/json")
            self.end_headers(); self.wfile.write(body); return
        return super().do_GET()

os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("open http://localhost:8080/index.html")
socketserver.TCPServer(("", 8080), H).serve_forever()
