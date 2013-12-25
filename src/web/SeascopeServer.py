#!/usr/bin/env python

# Copyright (c) 2014 Anil Kumar
# All rights reserved.
#
# License: BSD

import os
import subprocess
import threading
import time

import json
import socket

import BackendTool

from SocketServer import ThreadingMixIn
from BaseHTTPServer import HTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

server_conf_js = None

def setup_srvr_conf_js(host, port):
	global server_conf_js
	server_conf_js = '''var sinfo = {
				host: "%s",
				port: %s,
			}''' % (host, port)

class ThreadingServer(ThreadingMixIn, HTTPServer):
    pass

class RequestHandler(SimpleHTTPRequestHandler):
	def parse_path(self):
		import urlparse
		p = urlparse.urlparse(self.path)
		print 'path', p.path
		if p.path.startswith('/'):
			path = p.path
			if path == '/':
				path = '/h.html'
			if path == '/js/server_conf.js':
				self.reply_to_GET(server_conf_js, 'text/javascript');
			wp = 'www' + path
			if os.path.exists(wp):
				data = open(wp).read()
				cont_type = 'text/html'
				if p.path.endswith('.js'):
					cont_type = 'text/javascript'
				self.reply_to_GET(data, cont_type);
				return None
		if p.path != '/q':
			print 'not /q instead', p.path
			return
		print 'p.query', p.query
		qd = urlparse.parse_qs(p.query)
		for k in qd.keys():
			v = qd[k]
			if len(v) == 0:
				assert false
			qd[k] = v[-1]
		print 'qd', qd
		#import json
		#d = json.loads(qd)
		#print 'd', d
		return qd

	def reply_to_GET(self, qres, cont_type):
		rh = self
		rh.send_response(200)
		#rh.send_header('Content-type', 'text/plain')
		rh.send_header('Content-type', cont_type)
		rh.send_header('Content-length', len(qres))
		rh.end_headers()
		rh.wfile.write(qres)

	def do_GET(self):
		qd = self.parse_path()
		if not qd:
			return
		outd = BackendTool.run_op(qd)
		data = json.dumps(outd)
		if 'callback' in qd:
			data = '%s(%s);' % (qd['callback'], data)
		self.reply_to_GET(data, 'application/json')

def start_server(host, port):
	setup_srvr_conf_js(host, port)

	print 'starting server at http://%s:%s' % (host, port)
	try:
		ts = ThreadingServer((host, port), RequestHandler)
		ts.serve_forever()
	except Exception as e:
		print e

	print 'exiting'
