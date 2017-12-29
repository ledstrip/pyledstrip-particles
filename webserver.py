#!/usr/bin/env python3

import cgi
import http.server
import json
import socketserver

__PORT = 8000
launches = []


class Handler(http.server.BaseHTTPRequestHandler):
	def send_file(self, status, file):
		content = open(file, "rb").read()
		self.send_response(status)
		self.send_header("Content-Type", "text/html")
		self.send_header("Content-Length", len(content))
		self.end_headers()
		self.wfile.write(content)

	def do_GET(self):
		if self.path == "/":
			self.send_file(200, "web/index.html")
		else:
			self.send_file(404, "web/404.html")

	def do_POST(self):
		global launches
		if self.path == "/launch":
			self.send_response(204)
			ctype, pdict = cgi.parse_header(self.headers["content-type"])
			if ctype == "application/json":
				content = json.loads(self.rfile.read(int(self.headers["content-length"])).decode("utf-8"))
				launches.append((content["hue"] / 360, content["velocity"], content["direction"]))
		else:
			self.send_file(404, "web/404.html")


socketserver.TCPServer.allow_reuse_address = True
__httpd = socketserver.TCPServer(("", __PORT), Handler)
__httpd.timeout = 0


def step():
	global launches
	__httpd.handle_request()
	l = launches
	launches = []
	return l


if __name__ == '__main__':
	print("entering test mode")
	while True:
		l = step()
		if len(l) > 0:
			print(l)
