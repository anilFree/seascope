import sys
import os
import string

from PyQt4 import QtGui, QtCore, uic

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class DebugInfoEntry(QLabel):
	def __init__(self, parent=None):
		QLabel.__init__(self)
		self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)

	#def add_result_continue(self):
		#self.add_result(self.name, self.res)

	def add_result(self, name, res):
		#text = '<b>' + name + '</b>';
		text = name;
		for line in res:
			text += '\n    ' + str(''.join(line))
		self.setText(str(text))

class DebugWindow(QMainWindow):
	dlg = None

	def __init__(self, parent=None):
		QMainWindow.__init__(self)

		print 'new dbg window'
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
		print 'closeEvent'
		DebugWindow.dlg = None

def show_dbg_dialog():
	if (DebugWindow.dlg == None):
		DebugWindow.dlg = DebugWindow()
	DebugWindow.dlg.run_dialog()


def connect_to_cs_sig_res(sig_res):
	if (DebugWindow.dlg == None):
		return
	entry = DebugInfoEntry()
	DebugWindow.dlg.append_widget(entry)
	sig_res.connect(entry.add_result)
