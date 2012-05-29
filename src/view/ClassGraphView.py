#!/usr/bin/python

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtSvg import *
import os

from backend.plugins.PluginBase import PluginProcess

class CallGraphProcess(PluginProcess):
	def __init__(self, wdir, rq):
		PluginProcess.__init__(self, wdir)
		self.name = 'call graph process'
		if rq == None:
			rq = ['', '']
		self.cmd_str = rq[0]
		self.req = rq[1]

	def parse_result(self, text, sig):
		return [text]


class ClassGraphWidget(QWidget):
	def __init__(self, parent, cmd_func, cmd_id, cmd_opt):
		QWidget.__init__(self, parent)
		self.is_busy = False
		self.is_done = False
		self.cmd_func = cmd_func
		self.cmd_id = cmd_id
		self.cmd_opt = cmd_opt

	def startQuery(self, req, proj_dir):
		if self.is_done:
			return

		tool_path = os.path.join('tools', 'ClassGraph.py')
		pargs = ['python', tool_path, '-p', proj_dir, req]
		sig_res = CallGraphProcess('.', None).run_query_process(pargs, req)
		sig_res[0].connect(self.clgraph_add_result)
		self.is_busy = True
		self.show_progress_bar()

	def clgraph_add_result(self, req, res):
		self.is_busy = False
		self.is_done = True
		self.remove_progress_bar()

		self.vlay1 = QVBoxLayout()
		self.vlay2 = QVBoxLayout()
		
		self.scrolla = QScrollArea()
		self.setLayout(self.vlay1)
		self.vlay1.addWidget(QLabel(req))
		self.vlay1.addWidget(self.scrolla)
		
		self.svgw = QSvgWidget()
		self.scrolla.setLayout(self.vlay2)
		self.vlay2.addWidget(self.svgw)
		self.svgw.load(QByteArray(res[0]))

	def show_progress_bar(self):
		self.pbar = QProgressBar(self)
		self.pbar.setMinimum(0)
		self.pbar.setMaximum(0)
		self.pbar.show()

	def remove_progress_bar(self):
		if (self.pbar):
			self.pbar.setParent(None)
			self.pbar = None

class ClassGraphWindow(QMainWindow):
	parent = None

	def __init__(self, req, proj_dir,  cmd_func, cmd_args, cmd_opt):
		QMainWindow.__init__(self, ClassGraphWindow.parent)
		self.req = req
		self.proj_dir = proj_dir

		self.setWindowTitle(req)

		self.setFont(QFont("San Serif", 8))

		w = QWidget()
		self.setCentralWidget(w)
		self.vlay = QVBoxLayout()
		w.setLayout(self.vlay)

		self.sw = QStackedWidget()

		self.hlay = QHBoxLayout()
		self.vlay.addLayout(self.hlay)
		self.vlay.addWidget(self.sw)
		
		self.bgrp = QButtonGroup()
		self.bgrp.buttonClicked.connect(self.set_current)
		self.bgrp.setExclusive(True)

		self.btn = []
		self.ctree = []
		for inx in range(len(cmd_args)):
			# cmd format: [ cmd_id, cmd_str, cmd_tip ]
			cmd = cmd_args[inx]

			btn = QToolButton()
			btn.setText(cmd[1])
			btn.setToolTip(cmd[2])
			#btn.setFlat(True)
			btn.setCheckable(True)
			self.bgrp.addButton(btn, inx)
			self.hlay.addWidget(btn)

			ct = ClassGraphWidget(self, cmd_func, cmd[0], cmd_opt)
			self.sw.addWidget(ct)

			self.btn.append(btn)
			self.ctree.append(ct)
		self.hlay.addStretch(0)
		self.set_current(self.btn[0])

	def set_current(self, btn):
		inx = self.bgrp.id(btn)
		self.btn[inx].setChecked(True)
		self.sw.setCurrentIndex(inx)
		ct = self.ctree[inx]
		ct.setFocus()
		
		ct.startQuery(self.req, self.proj_dir)



def create_page(req, proj_dir, cmd_func, cmd_args, cmd_opt):
	w = ClassGraphWindow(req, proj_dir, cmd_func, cmd_args, cmd_opt)
	w.resize(500, 300)
	w.show()
