# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import re, os

from PyQt4 import QtGui, QtCore, uic

from PyQt4.QtGui import *
from PyQt4.QtCore import *

fc_plugins = []
fc_dict = {}

def _load_plugins(module, directory):
	pluginImports = __import__(module, globals(), locals())
	print 'Scanning for view plugins...'
	plist = []
	pdict = {}
	for i in sorted(os.listdir(directory)):
		path = os.path.join( directory, i, '__init__.py' )
		if os.path.isfile( path ):
			p = __import__( '%s.%s' % (module, i), globals(), locals(), ['*'] )
			plist.append(p)
			pdict[p.name()] = p
			if not hasattr(p, 'priority'):
				p.priority = 0 
	plist = sorted(plist, key=lambda p: p.priority, reverse=True)
	for p in plist:
		print '\t', p.name()
	return (plist, pdict)

def load_plugins():
	global fc_plugins, fc_dict
	(fc_plugins, fc_dict) = _load_plugins('view.filecontext.plugins', 'view/filecontext/plugins')

def run_plugins(filename, parent):
	for p in fc_plugins:
		if not hasattr(p, 'cmd_name'):
			p.run_plugin(filename, parent)

