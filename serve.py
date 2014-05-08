#!/usr/bin/python

import BaseHTTPServer
import CGIHTTPServer
import cgitb;

cgitb.enable()  # Error reporting

server = BaseHTTPServer.HTTPServer
handler = CGIHTTPServer.CGIHTTPRequestHandler
server_address = ("", 8765)
handler.cgi_directories = ["/"]

httpd = server(server_address, handler)
httpd.serve_forever()
