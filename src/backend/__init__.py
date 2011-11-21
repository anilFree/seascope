import os
import sys
import re

from PyQt4 import QtGui, QtCore, uic

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import DialogManager

backend_plugins = []

def _load_plugins(module, directory):
	pluginImports = __import__(module, globals(), locals())
	print 'Scanning for plugins...'
	plist = []
	for i in os.listdir(directory):
		path = os.path.join( directory, i, '__init__.py' )
		if os.path.isfile( path ):
			p = __import__( '%s.%s' % (module, i), globals(), locals(), ['*'] )
			plist.append(p)
			print '\t', p.name()
	return plist

def load_plugins():
	global backend_plugins
	backend_plugins = _load_plugins('backend.plugins', 'backend/plugins')


from plugins.PluginBase import ProjectBase, ConfigBase, QueryBase, QueryUiBase

prj_actions = []
prj = None

def _proj_new_open():
	for act in prj_actions:
		act.setEnabled(True)

def proj_new():
	b = None
	for p in backend_plugins:
		if p.name() == 'cscope':
			b = p
			break
	if not b:
		print 'No backends'
		return None
	global prj
	assert not prj
	prj = b.project_class().prj_new()

	if prj:
		_proj_new_open()
	return prj != None

def proj_open(proj_path):
	b = []
	for p in backend_plugins:
		if p.is_your_prj(proj_path):
			b.append(p)
	if len(b) == 0:
		print "Project '%s': No backend is interested" % proj_path
		return
	if len(b) > 1:
		print "Project '%s': Many backends interested" % proj_path
		return
	print "Project '%s': Using %s backend" % (proj_path, b[0].name())

	global prj
	prj = b[0].project_class().prj_open(proj_path)

	if prj:
		_proj_new_open()
	return prj != None

def proj_close():
	global prj
	prj.prj_close()
	prj = None
	
	QueryUiBase.backend_menu.clear()
	QueryUiBase.backend_menu.setTitle('')
	for act in prj_actions:
		act.setEnabled(False)

def proj_is_open():
	return prj != None

def proj_name():
	return prj.prj_name() if prj else None

def proj_dir():
	return prj.prj_dir() if prj else None

def proj_src_files():
	return prj.prj_src_files()

def proj_conf():
	return prj.prj_conf()

def proj_settings_trigger():
	return prj.prj_settings_trigger()