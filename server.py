#!/usr/bin/env python3
"""
NSE Dashboard Server - serves static files and proxies Yahoo Finance API.
Usage: python server.py
Then open: http://localhost:8080
"""
import http.server
import urllib.request
import urllib.parse
import json
import os
import sys
from urllib.parse import urlparse, quote

PORT = 8080
YAHOO_BASE = "https://query2.finance.yahoo.com/v8/finance/chart"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    """Serves static files AND proxies Yahoo Finance at /api/quote/"""

    def do_GET(self):
        if self.path.startswith('/api/quote/'):
            symbol = self.path[len('/api/quote/'):]
            self.proxy_yahoo(symbol)
        elif self.path.startswith('/api/history/'):
            symbol = self.path[len('/api/history/'):]
            self.proxy_yahoo(symbol, range='1y')
        elif self.path == '/' or self.path == '':
            self.send_file('NSE.html')
        else:
            super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def send_file(self, filename):
        """Serve a file from the current directory"""
        try:
            with open(filename, 'rb') as f:
                data = f.read()
            self.send_response(200)
            if filename.endswith('.html'):
                self.send_header('Content-Type', 'text/html; charset=utf-8')
            elif filename.endswith('.css'):
                self.send_header('Content-Type', 'text/css')
            elif filename.endswith('.js'):
                self.send_header('Content-Type', 'application/javascript')
            elif filename.endswith('.json'):
                self.send_header('Content-Type', 'application/json')
            else:
                self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'File not found')

    def proxy_yahoo(self, symbol, range='5d'):
        """Fetch from Yahoo Finance and return as JSON (with CORS headers)"""
        url = f"{YAHOO_BASE}/{quote(symbol)}?interval=1d&range={range}"
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': USER_AGENT}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode('utf-8')
                # Validate it's actual JSON
                json.loads(raw)  # throws if invalid
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(raw.encode('utf-8'))
        except json.JSONDecodeError:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid response from Yahoo", "symbol": symbol}).encode('utf-8'))
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Yahoo HTTP {e.code}", "symbol": symbol}).encode('utf-8'))
        except Exception as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e), "symbol": symbol}).encode('utf-8'))

    def log_message(self, format, *args):
        """Quieter logging"""
        msg = format % args
        if '/api/' in msg or '304' in msg:
            pass  # skip verbose API logs
        else:
            print(f"[{self.log_date_time_string()}] {msg}", file=sys.stderr)


if __name__ == '__main__':
    # Change to the script's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    server = http.server.ThreadingHTTPServer(('0.0.0.0', PORT), ProxyHandler)
    print(f"==================================================")
    print(f"  NSE DASHBOARD SERVER RUNNING")
    print(f"")
    print(f"  http://localhost:{PORT}")
    print(f"  http://127.0.0.1:{PORT}")
    print(f"")
    print(f"  Press Ctrl+C to stop")
    print(f"==================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
