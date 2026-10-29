#
# AWS Lambda MicroVM server.
#
# Lambda starts this file while it builds the MicroVM image, snapshots it, and
# sends requests for each MicroVM to port 8080. Requests to the lifecycle hooks
# are answered here. Every other request is passed to yourFunction in handler.py:
# fields from the JSON body and query string are copied onto the request, and the
# SAAF attributes it returns are sent back as JSON.
#
# Requests are handled one at a time, so CPU and memory deltas belong to one request.
#
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlsplit, parse_qsl

import handler

PORT = 8080
HOOKS = "/aws/lambda-microvms/runtime/v1/"
RESERVED = {"method", "path", "query", "headers", "body"}


def apply_fields(target, source):
    for key, value in source.items():
        if key not in RESERVED and key not in target:
            target[key] = value


class Server(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def read_body(self):
        if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
            chunks = []
            while True:
                size = int(self.rfile.readline().split(b";")[0], 16)
                if size == 0:
                    self.rfile.readline()
                    break
                chunks.append(self.rfile.read(size))
                self.rfile.readline()
            return b"".join(chunks).decode("utf-8")
        length = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(length).decode("utf-8")

    def send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def handle_request(self):
        url = urlsplit(self.path)
        text = self.read_body()

        # Lambda calls /ready during the image build, before the snapshot, and /run
        # when a MicroVM starts from the snapshot, with that MicroVM's ID.
        if url.path == HOOKS + "ready":
            self.send_json(200, {})
            return
        if url.path == HOOKS + "run":
            try:
                microvm_id = json.loads(text).get("microvmId", "")
            except ValueError:
                microvm_id = ""
            with open("/tmp/microvm-id", "w") as file:
                file.write(microvm_id)
            self.send_json(200, {})
            return

        try:
            body = json.loads(text) if text else {}
        except ValueError:
            self.send_json(400, {"error": "Request body is not valid JSON"})
            return

        query = dict(parse_qsl(url.query))
        request = {
            "method": self.command,
            "path": url.path,
            "query": query,
            "headers": dict(self.headers),
            "body": body
        }
        if isinstance(body, dict):
            apply_fields(request, body)
        apply_fields(request, query)

        try:
            self.send_json(200, handler.yourFunction(request, {}))
        except Exception as e:
            self.send_json(500, {"error": str(e)})

    do_GET = handle_request
    do_POST = handle_request
    do_PUT = handle_request
    do_DELETE = handle_request


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Server)
    print("SAAF MicroVM server listening on port " + str(PORT), flush=True)
    server.serve_forever()
