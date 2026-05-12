#!/usr/bin/env python3
"""
Tiny helper for ppm-manager.html.

Why this exists:
  Browsers refuse to call Facilio's API directly from a file on your computer
  (a security rule called CORS). This helper runs a small server on your own
  machine, serves ppm-manager.html, and forwards its requests to Facilio.

How to run:
  1. Open Terminal (Cmd+Space, type "Terminal", hit Return).
  2. Drag this start.py file onto the Terminal window — its full path appears.
  3. Type "python3 " in front of that path, then hit Return.
     (Or: cd to the folder containing this file and run: python3 start.py)
  4. Your browser opens automatically. Done.

Stop it:
  Press Ctrl+C in the Terminal window. Closing the Terminal window also stops it.
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
import threading
import webbrowser
import socket

PORT = 8765
# Look for index.html first (matches the GitHub Pages layout); fall back to the
# old ppm-manager.html for backwards compatibility.
HTML_FILE_CANDIDATES = ["index.html", "ppm-manager.html"]
HTML_FILE = "index.html"  # resolved at startup in main()
ALLOWED_HEADERS = ("x-api-key", "x-device-type", "x-version", "x-org-group", "Content-Type", "content-type")


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    # Quieter logging
    def log_message(self, fmt, *args):
        sys.stderr.write("[server] " + (fmt % args) + "\n")

    def do_GET(self):
        if self.path.startswith("/proxy"):
            self._proxy("GET", None)
            return
        if self.path in ("/", ""):
            self.path = "/" + HTML_FILE
        return super().do_GET()

    def do_POST(self):    self._proxy("POST",   self._read_body())
    def do_PATCH(self):   self._proxy("PATCH",  self._read_body())
    def do_DELETE(self):  self._proxy("DELETE", self._read_body())
    def do_PUT(self):     self._proxy("PUT",    self._read_body())

    def _read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n > 0 else None

    def _proxy(self, method, body):
        try:
            qs = urllib.parse.urlparse(self.path).query
            url = urllib.parse.parse_qs(qs).get("url", [None])[0]
            if not url:
                self.send_error(400, "missing url query parameter")
                return
            url = urllib.parse.unquote(url)

            req = urllib.request.Request(url, data=body, method=method)
            for h in ALLOWED_HEADERS:
                v = self.headers.get(h)
                if v:
                    req.add_header(h, v)

            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    self.send_response(resp.status)
                    ct = resp.headers.get("Content-Type", "application/json")
                    self.send_header("Content-Type", ct)
                    self.end_headers()
                    self.wfile.write(resp.read())
            except urllib.error.HTTPError as e:
                # Forward error responses with the original status code & body
                self.send_response(e.code)
                self.send_header("Content-Type", e.headers.get("Content-Type", "application/json"))
                self.end_headers()
                try:
                    self.wfile.write(e.read())
                except Exception:
                    pass
        except urllib.error.URLError as e:
            self.send_error(502, "Upstream connection failed: %s" % e)
        except Exception as e:
            self.send_error(500, "Proxy error: %s" % e)


def main():
    global HTML_FILE
    here = os.path.dirname(os.path.abspath(__file__))
    os.chdir(here)
    # Pick the first HTML file that exists in this folder.
    HTML_FILE = next((f for f in HTML_FILE_CANDIDATES if os.path.exists(f)), None)
    if not HTML_FILE:
        print("Error: neither index.html nor ppm-manager.html found next to this script.")
        print("Make sure the HTML file and start.py are in the same folder.")
        sys.exit(1)
    print("  Serving: %s" % HTML_FILE)

    port = PORT
    # If the chosen port is taken, pick the next free one.
    for p in range(PORT, PORT + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", p))
            port = p
            break
        except OSError:
            continue

    url = "http://localhost:%d/" % port
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    print("\n  PPM Manager is running.")
    print("  Open in your browser if it doesn't auto-open:")
    print("    " + url)
    print("\n  Stop with Ctrl+C, or just close this window.\n")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), ProxyHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
