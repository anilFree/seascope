# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os
import sys
import re

from PyQt4 import QtGui, QtCore, uic

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import DialogManager
from plugins import PluginHelper

backend_plugins = []
backend_dict = {}

def _load_plugins(module, directory):
	pluginImports = __import__(module, globals(), locals())
	print 'Scanning for backend plugins...'
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
	global backend_plugins, backend_dict
	(backend_plugins, backend_dict) = _load_plugins('backend.plugins', 'backend/plugins')


from plugins.PluginBase import ProjectBase, ConfigBase, QueryBase, QueryUiBase

prj_actions = []
prj = None

def _proj_new_open():
	for act in prj_actions:
		act.setEnabled(True)

class ProjectNewDialog(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		self.ui = uic.loadUi('ui/proj_new.ui', self)
		self.backend_lw.currentRowChanged.connect(self.currentRowChanged_cb)

	def currentRowChanged_cb(self, row):
		if row == -1:
			return
		bname = str(self.backend_lw.currentItem().text())
		b = backend_dict[bname]
		try:
			self.descr_te.setText(b.description())
		except:
			self.descr_te.setText('')

	def run_dialog(self):
		bi = [ b.name() for b in backend_plugins]
		self.backend_lw.addItems(bi)
		self.backend_lw.setCurrentRow(0)
		if self.exec_() == QDialog.Accepted:
			bname = str(self.backend_lw.currentItem().text())
			return (backend_dict[bname])
		return None

def msg_box(msg):
	QMessageBox.warning(None, "Seascope", msg, QMessageBox.Ok)

def proj_new():
	if len(backend_plugins) == 0:
		msg_box('No backends are available/usable')
	dlg = ProjectNewDialog()
	b = dlg.run_dialog()
	if b == None:
		return

	global prj
	assert not prj
	prj = b.project_class().prj_new()

	if prj:
		_proj_new_open()
	return prj != None

def proj_open(proj_path):
	be = []
	for p in backend_plugins:
		if p.is_your_prj(proj_path):
			be.append(p)
	if len(be) == 0:
		msg = "Project '%s': No backend is interested" % proj_path
		msg_box(msg)
		return
	if len(be) > 1:
		msg = "Project '%s': Many backends interested" % proj_path
		for b in be:
			msg += '\n\t' + b.name()
		msg += '\n\nGoing ahead with: ' + be[0].name()
		msg_box(msg)

	b = be[0]
	print "Project '%s': using '%s' backend" % (proj_path, b.name())

	global prj
	prj = b.project_class().prj_open(proj_path)

	if prj:
		_proj_new_open()
	return prj != None

def proj_close():
	global prj
	prj.prj_close()
	prj = None
	
	PluginHelper.backend_menu.clear()
	PluginHelper.backend_menu.setTitle('')
	for act in prj_actions:
		act.setEnabled(False)

	from plugins import CtagsCache
	CtagsCache.flush()

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