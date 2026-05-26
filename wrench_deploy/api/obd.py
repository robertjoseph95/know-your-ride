from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._send(200, {
            "available": False,
            "connected": False,
            "message": ("OBD-II diagnostics require the local wrench_serve.py server connected to a "
                        "physical ELM327 adapter in your vehicle. This cloud deployment cannot reach "
                        "your car's OBD-II port. Run wrench_serve.py locally to use live diagnostics."),
        })

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
