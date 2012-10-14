#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import filecontext

class FileContextView(QTabWidget):
	sig_goto_line = pyqtSignal(int)
	sig_ed_cursor_changed = pyqtSignal(int, int)

	def __init__(self, parent=None):
		QTabWidget.__init__(self)
		self.setTabPosition(QTabWidget.South)

	def add_page(self, page, title):
		page.sig_goto_line.connect(self.sig_goto_line)
		self.addTab(page, title)
		self.setCurrentWidget(page)

	def run(self, filename):
		self.filename = filename
		filecontext.run_plugins(filename, self)

	def rerun(self, filename):
		inx = self.currentIndex()
		self.clear()
		self.run(filename)
		self.setCurrentIndex(inx)

	def focus_search_ctags(self):
		for inx in range(self.count()):
			page = self.widget(inx)
			if hasattr(page, 'le') and hasattr(page.le, 'setFocus'):
				self.setCurrentWidget(page)
				page.le.setFocus()
				break

	def get_already_opened_cmd_list(self):
		a_cmd_list = []
		for inx in range(self.count()):
			page = self.widget(inx)
			if hasattr(page, 'cmd'):
				a_cmd_list.append(page.cmd)
		return a_cmd_list

	def get_plugin_cmd_list(self):
		a_cmd_list = self.get_already_opened_cmd_list()
		cmd_list = []
		for p in filecontext.fc_plugins:
			if not hasattr(p, 'cmd_name'):
				continue
			cmd_name = p.cmd_name()
			if not cmd_name:
				continue
			if not isinstance(cmd_name, list):
				if cmd_name == '':
					continue
				cmd_name = [ cmd_name ]
			for cmd in cmd_name:
				if cmd in a_cmd_list:
					continue
				cmd_list.append((cmd, p))
		return cmd_list

	def menu_act_triggered_cb(self, act):
		act.plugin.run_plugin(self.filename, self, cmd=act.cmd_name)

	def mousePressEvent(self, m_ev):
		cmd_list = self.get_plugin_cmd_list()
		if len(cmd_list) == 0:
			return
		if (m_ev.button() == Qt.RightButton):
			# setup popup menu
			pmenu = QMenu()
			pmenu.triggered.connect(self.menu_act_triggered_cb)
			for (cmd_name, p) in cmd_list:
				act = pmenu.addAction(cmd_name)
				act.plugin = p
				act.cmd_name = cmd_name
			pmenu.exec_(QCursor.pos())
			pmenu = None
