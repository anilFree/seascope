#!/usr/bin/env python

# Copyright (c) 2014 Anil Kumar
# All rights reserved.
#
# License: BSD

import sys
sys.dont_write_bytecode = True

import os
import socket

import BackendTool
import SeascopeServer

def start(plist, host, port):
	if not BackendTool.load_projects(plist):
		sys.exit(-1)

	SeascopeServer.start_server(host, port)

if __name__ == '__main__':
	import optparse
	usage = "usage: %prog [options] [project_path ...]"
	op = optparse.OptionParser(usage=usage)
	op.add_option("-H", "--host", dest="host",             default="127.0.0.1", help="Host")
	op.add_option("-P", "--port", dest="port", type='int', default=8650,        help="Port")
	(options, args) = op.parse_args()

	if options.port > 65535:
		print 'options.port > 65535'
		sys.exit(-1)

	plist = []
	for p in args:
		if not os.path.isdir(p):
			print '%p is not a directory'
			sys.exit(-2)
		plist.append(os.path.abspath(p))

	#options.host = socket.gethostname()
	start(plist, options.host, options.port)
