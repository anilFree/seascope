#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.QtSvg import *
import os
import sys

if __name__ == '__main__':
	import sys
	import os
	app_dir = os.path.dirname(os.path.realpath(__file__))
	os.chdir(app_dir)
	sys.path.insert(0, os.path.abspath('..'))
	os.chdir(os.path.abspath('..'))

from backend.plugins.PluginBase import PluginProcess

class FileFuncGraphProcess(PluginProcess):
	def __init__(self, wdir, rq):
		PluginProcess.__init__(self, wdir, rq)
		self.name = 'call graph process'

	def parse_result(self, text, sig):
		return [text]


class FileFuncGraphWidget(QWidget):
	def __init__(self, parent, cmd_func, cmd_id, cmd_opt):
		QWidget.__init__(self, parent)
		self.is_busy = False
		self.is_done = False
		self.cmd_func = cmd_func
		self.cmd_id = cmd_id
		self.cmd_opt = cmd_opt
		self.is_debug = os.getenv('SEASCOPE_FILE_FUNC_GRAPH_VIEW_DEBUG')

		self.vlay1 = QVBoxLayout()
		self.setLayout(self.vlay1)
		#self.hlay1 = QHBoxLayout()
		#self.vlay1.addLayout(self.hlay1)
		#self.add_buttons(self.hlay1)
		self.lbl = QLabel()
		self.vlay1.addWidget(self.lbl)

		self.vlay2 = QVBoxLayout()
		self.scrolla = QScrollArea()
		self.scrolla.setLayout(self.vlay2)
		self.vlay1.addWidget(self.scrolla)

		self.warn_experimental_lbl = QLabel('Warning: this is an EXPERIMENTAL feature based on cscope, might not work on all files for now.')
		self.warn_experimental_lbl.setStyleSheet("QLabel { color : red; }")
		self.vlay1.addWidget(self.warn_experimental_lbl)

	def startQuery(self, req, dname, proj_dir, inx):
		if self.is_done:
			return

		name = req if req else dname
		labelList = [
			'File functions graph(%s)' % name,
			'File functions and external graph(%s)' %name,
			'Directory functions graph(%s)' % os.path.dirname(name),
			'Directory functions and external graph(%s)' % os.path.dirname(name)
		]
		self.lbl.setText(labelList[inx])

		tool_path = os.path.join('tools', 'FileFuncGraph.py')
		pargs = [sys.executable, tool_path]
		if inx == 0:
			pass
		elif inx == 1:
			pargs += ['-e']
		elif inx == 2:
			dname = os.path.dirname(name)
		elif inx == 3:
			pargs += ['-e']
			dname = os.path.dirname(name)

		pargs += ['-d', dname]
		sig_res = FileFuncGraphProcess('.', None).run_query_process(pargs, req)
		sig_res[0].connect(self.clgraph_add_result)
		self.is_busy = True
		self.show_progress_bar()

	def set_current(self, btn):
		inx = self.bgrp.id(btn)
		#self.btn[inx].setChecked(True)
		#print 'inx clicked', inx
		if inx == 0:
			print self.svgw.renderer().defaultSize()
			self.svgw.setMinimumSize(0, 0)
			self.svgw.setMinimumSize(self.svgw.sizeHint())
			#self.svgw.setMaximumSize(self.svgw.sizeHint())
			print self.scrolla.sizeHint()
		if inx == 1:
			print self.svgw.renderer().defaultSize()
			self.svgw.setMinimumSize(0, 0)
			#self.svgw.setMaximumSize(self.svgw.sizeHint())
			print self.scrolla.sizeHint()
		if inx == 2:
			print self.svgw.renderer().defaultSize()
			self.svgw.setMinimumSize(0, 0)
			self.svgw.resize(self.scrolla.size())
			#self.svgw.setMaximumSize(self.svgw.sizeHint())
			print self.scrolla.sizeHint()

	def add_buttons(self, hlay):
		self.bgrp = QButtonGroup()
		self.bgrp.buttonClicked.connect(self.set_current)
		self.bgrp.setExclusive(True)
		for inx in range(3):
			btn = QToolButton()
			btn.setText(str(inx))
			btn.setToolTip(str(inx))
			#btn.setFlat(True)
			btn.setCheckable(True)
			self.bgrp.addButton(btn, inx)
			hlay.addWidget(btn)

	def clgraph_add_result(self, req, res):
		if self.is_debug:
			print res
		self.is_busy = False
		self.is_done = True
		self.remove_progress_bar()
		
		self.svgw = QSvgWidget()
		self.scrolla.setWidget(self.svgw)
		self.svgw.load(QByteArray(res[0]))
		
		#print self.svgw.renderer().defaultSize()
		sz = self.svgw.sizeHint()
		scale = 1
		if sz.width() > 1024:
			scale = 0.8
		self.svgw.setMinimumSize(sz.width() * scale, sz.height() * scale)
		#self.svgw.setMaximumSize(self.svgw.sizeHint())
		#print self.scrolla.sizeHint()

	def show_progress_bar(self):
		self.pbar = QProgressBar(self.scrolla)
		self.pbar.setMinimum(0)
		self.pbar.setMaximum(0)
		self.pbar.show()

	def remove_progress_bar(self):
		if self.pbar:
			self.pbar.hide()
			self.pbar.setParent(None)
			self.pbar = None

class FileFuncGraphWindow(QMainWindow):
	parent = None

	def __init__(self, req, dname, proj_dir, cmd_func, cmd_args, cmd_opt):
		QMainWindow.__init__(self, FileFuncGraphWindow.parent)
		self.req = req
		self.dname = dname
		self.proj_dir = proj_dir

		if req:
			self.setWindowTitle(req)
		else:
			self.setWindowTitle(dname)

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

			ct = FileFuncGraphWidget(self, cmd_func, cmd[0], cmd_opt)
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
		
		ct.startQuery(self.req, self.dname, self.proj_dir, inx)



def create_page(req, dname, proj_dir, cmd_func, cmd_args, cmd_opt):
	w = FileFuncGraphWindow(req, dname, proj_dir, cmd_func, cmd_args, cmd_opt)
	w.resize(900, 600)
	w.show()
	return w

if __name__ == '__main__':
	import optparse
	usage = "usage: %prog (-d <code_dir/file> | -p <idutils_proj>) [symbol]"
	op = optparse.OptionParser(usage=usage)
	op.add_option("-d", "--codedir", dest="code_dir", help="Code dir", metavar="CODE_DIR")
	op.add_option("-p", "--project", dest="id_path", help="Idutils project dir", metavar="PROJECT")
	(options, args) = op.parse_args()

	sym = ''
	dname = ''
	id_path = None

	if (not any([options.code_dir, options.id_path]) or
               all([options.code_dir, options.id_path])):
		print >> sys.stderr, 'Specify one among -d or -p'
		sys.exit(-1)

	if len(args):
		if len(args) != 1:
			print >> sys.stderr, 'Please specify a symbol'
			sys.exit(-4)
		sym = args[0]

	if options.code_dir:
		dname = options.code_dir
		if not os.path.exists(dname):
			print >> sys.stderr, '"%s": does not exist' %  dname
			sys.exit(-2)
	if options.id_path:
		if not sym:
			print >> sys.stderr, '-p option needs a symbol'
			sys.exit(-3)
		id_path = os.path.normpath(options.id_path)
		if not os.path.exists(os.path.join(id_path, 'ID')):
			print >> sys.stderr, 'idutils project path does not exist'
			sys.exit(-4)

	app = QApplication(sys.argv)
	cmd_args = [
		['FFGRAPH',    'F',   'File functions graph'],
		['FFGRAPH_E',  'F+E', 'File functions + external graph'],
		['FFGRAPH_D',  'D',   'Directory functions graph'],
		['FFGRAPH_DE', 'D+E', 'Directory functions + external graph']
	]

	w = create_page(sym, dname, id_path, None, cmd_args, None)

	sys.exit(app.exec_())
