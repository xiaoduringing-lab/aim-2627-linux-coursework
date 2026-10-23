"""Small local HTTP service; no external network or third-party packages."""
import argparse
import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

parser = argparse.ArgumentParser()
parser.add_argument("config")
args = parser.parse_args()
config = {}
with open(args.config) as stream:
    for line in stream:
        if "=" in line and not line.startswith("#"):
            key, value = line.strip().split("=", 1)
            config[key] = value


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = b"SENTRY READY\n" if self.path == config["route"] else b"NOT FOUND\n"
        self.send_response(200 if self.path == config["route"] else 404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


server = ThreadingHTTPServer((config["bind"], int(config["port"])), Handler)


def stop(signum, frame):
    threading.Thread(target=server.shutdown, daemon=True).start()


signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
print(f"LISTEN {config['bind']}:{config['port']} {config['route']}", flush=True)
try:
    server.serve_forever(poll_interval=0.1)
finally:
    server.server_close()
    print("SERVICE STOP", flush=True)
