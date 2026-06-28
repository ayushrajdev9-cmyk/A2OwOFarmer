from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>A2 OWO FARMER</h1><p>Made by Ayush Rajdev &amp; Anzar Iqbal</p><p>Bot is running!</p>")
    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 6909))
    srv = HTTPServer(('0.0.0.0', port), Handler)
    print(f"Dashboard running on port {port}")
    srv.serve_forever()
