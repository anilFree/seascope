# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import sys
import os
import string

from PyQt4 import QtGui, QtCore, uic

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class DebugInfoEntry(QFrame):
	def __init__(self, parent=None):
		QFrame.__init__(self)
		self.vlay = QVBoxLayout()
		self.setLayout(self.vlay)

	#def add_result_continue(self):
		#self.add_result(self.name, self.res)

	def add_result(self, cmd, out, err):
		#self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
		self.cmd_lbl = QLabel()
		self.cmd_lbl.setText(cmd)
		self.vlay.addWidget(self.cmd_lbl)

		#if err != None and err != '':
			#self.err_lbl = QLabel()
			#self.err_lbl.setText('Error: ' + err)
			#self.vlay.addWidget(self.err_lbl)

		#self.res_lbl = QLabel()
		#self.res_lbl.setText(out)
		#self.vlay.addWidget(self.res_lbl)
		#self.res_lbl.hide()

class DebugWindow(QMainWindow):
	dlg = None

	def __init__(self, parent=None):
		QMainWindow.__init__(self, parent)

		self.ui = uic.loadUi('ui/debug.ui', self)
		self.vlay = self.ui.dbg_widget.layout()

	def append_widget(self, w):
		self.vlay.addWidget(w)

	def run_dialog(self):
		self.ui.show()
		vbar = self.ui.dbg_scroll_area.verticalScrollBar()
		vbar.setValue(vbar.maximum())
		self.ui.show()
	
	def closeEvent(self, e):
		DebugWindow.dlg = None

def show_dbg_dialog(parent):
	if (DebugWindow.dlg == None):
		DebugWindow.dlg = DebugWindow(parent)
	DebugWindow.dlg.run_dialog()


def connect_to_sig(sig_res):
	if (DebugWindow.dlg == None):
		return
	entry = DebugInfoEntry()
	DebugWindow.dlg.append_widget(entry)
	sig_res.connect(entry.add_result)
