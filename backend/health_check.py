import http.server
import socketserver
import json

PORT = 8000

class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"status": "healthy", "version": "1.0.0", "app": "Viral Video SaaS"}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        return

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), HealthCheckHandler) as httpd:
        print(f"Server running on port {PORT}")
        httpd.serve_forever()
