#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class GenericResItem(QTreeWidgetItem):
	def __init__(self, li):
		QTreeWidgetItem.__init__(self, li)
	def column_val(self, col):
		return str(self.data(col, Qt.DisplayRole).toString())
	def line_val(self):
		return (int(self.column_val(1)))

class GenericRes(QTreeWidget):
	def __init__(self, parent=None):
		QTreeWidget.__init__(self)
		
		self.setColumnCount(1)
		self.setHeaderLabels(['Result'])

		#self.setMinimumHeight(200)
		self.setMinimumWidth(50)

		self.setFont(QFont("San Serif", 8))
		
		self.setIndentation(-2)

		self.setAllColumnsShowFocus(True)

	def add_result(self, res):
		for line in res:
			item = GenericResItem([line])
			self.addTopLevelItem(item)

class GenericFileCmdPage(QWidget):
	sig_goto_line = pyqtSignal(int)

	def __init__(self, parent=None):
		QWidget.__init__(self)
		self.ct = GenericRes(self)
		vlay = QVBoxLayout()
		#self.lbl = QLabel()
		#vlay.addWidget(self.lbl)
		vlay.addWidget(self.ct)
		self.setLayout(vlay)

		self.ct.itemActivated.connect(self.ct_itemActivated)

	def ct_itemActivated(self, item):
		try:
			line = int(str(item.data(1, Qt.DisplayRole).toString()))
		except:
			return
		self.sig_goto_line.emit(line)

	@staticmethod
	def run_plugin(cmd, filename, parent):
		if '%f' in cmd:
			args = cmd.replace('%f', filename)
			args = args.strip().split()
		else:
			args = cmd.strip().split()
			args.append(filename)
		import subprocess
		try:
			proc = subprocess.Popen(args, stdout=subprocess.PIPE)
			(res, err_data) = proc.communicate()
		except Exception as e:
			res = '%s\n%s' % (' '.join(args), str(e))
		import re
		res = [ x.strip() for x in re.split('\r?\n', res.strip()) ]
		
		page = GenericFileCmdPage(parent)
		page.cmd = cmd
		#page.lbl.setText(' '.join(args))
		page.ct.add_result(res)
		parent.add_page(page, cmd)

def cmd_name():
	cmd_list = [
		#'stat',
		#'ls %f',
		#'ls %f %f'
	]
	import os
	cmd = os.getenv('SEASCOPE_FC_CUSTOM_CMD')
	if cmd:
		cmd_list += [ x.strip() for x in cmd.split(';') ]
	return list(set(cmd_list))

def run(filename, parent, cmd=None):
	if cmd:
		cmd_list = [ cmd ]
	else:
		cmd_list = cmd_name()
	for cmd in cmd_list:
		GenericFileCmdPage.run_plugin(cmd, filename, parent)
