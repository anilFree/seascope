#!/usr/bin/env python

# Copyright (c) 2014 Anil Kumar
# All rights reserved.
#
# License: BSD

import sys
import os
import subprocess
import threading
import time

import json
import socket
import signal

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
	allow_reuse_address = True
	daemon_threads = True

is_debug = os.getenv('SEASCOPE_WEB_DEBUG')

class RequestHandler(SimpleHTTPRequestHandler):
	def parse_path(self):
		import urlparse
		p = urlparse.urlparse(self.path)
		if is_debug:
			print 'path', p.path
		if p.path.startswith('/'):
			path = p.path
			if path == '/':
				path = '/h.html'
			if path == '/js/server_conf.js':
				self.reply_to_GET(server_conf_js, 'text/javascript');
				return None
			wp = 'www' + path
			if os.path.exists(wp):
				data = open(wp).read()
				cont_type = 'text/html'
				if p.path.endswith('.js'):
					cont_type = 'text/javascript'
				self.reply_to_GET(data, cont_type);
				return None
		if p.path != '/q':
			if is_debug:
				print 'not /q instead', p.path
			return
		if is_debug:
			print 'p.query', p.query
		qd = urlparse.parse_qs(p.query)
		for k in qd.keys():
			v = qd[k]
			if len(v) == 0:
				print 'len(v) == 0', k, v
				continue
			qd[k] = v[-1]
		if is_debug:
			print 'qd', qd
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
		try:
			data = json.dumps(outd, ensure_ascii=False)
			if 'callback' in qd:
				data = '%s(%s);' % (qd['callback'], data)
			self.reply_to_GET(data, 'application/json')
		except Exception as e:
			print 'qd', qd
			print 'outd', outd
			print e
			data = e
			return

def start_server(host, port):
	setup_srvr_conf_js(host, port)

	print 'starting server at http://%s:%s' % (host, port)
	try:
		ts = ThreadingServer((host, port), RequestHandler)

		def signal_handler(signal, frame):
			ts.socket.close()
			print 'got signal %s, exiting' % signal
			os._exit(0)
		signal.signal(signal.SIGINT, signal_handler)
		signal.signal(signal.SIGTERM, signal_handler)

		ts.serve_forever()
	except Exception as e:
		print e
		sys.exit(-1)

	print 'exiting'
