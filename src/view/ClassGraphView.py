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

class ClassGraphProcess(PluginProcess):
	def __init__(self, wdir, rq):
		PluginProcess.__init__(self, wdir, rq)
		self.name = 'call graph process'

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
		self.is_debug = os.getenv('SEASCOPE_CLASS_GRAPH_VIEW_DEBUG')

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

	def startQuery(self, req, dname, proj_type, inx):
		if self.is_done:
			return

		name = req if req else dname
		self.lbl.setText(['derived', 'base'][inx] + '(' + name + ')')

		tool_path = os.path.join('tools', 'ClassGraph.py')
		pargs = [sys.executable, tool_path]
		if inx == 1:
			pargs += ['-b']
		pargs += ['-d', dname]
		if proj_type:
			pargs += ['-t', proj_type]
		if req:
			pargs += [req]
		sig_res = ClassGraphProcess('.', None).run_query_process(pargs, req)
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

class ClassGraphWindow(QMainWindow):
	parent = None

	def __init__(self, req, dname, proj_type, cmd_func, cmd_args, cmd_opt):
		QMainWindow.__init__(self, ClassGraphWindow.parent)
		self.req = req
		self.dname = dname
		self.proj_type = proj_type

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
		
		ct.startQuery(self.req, self.dname, self.proj_type, inx)



def create_page(req, dname, proj_type, cmd_func, cmd_args, cmd_opt):
	w = ClassGraphWindow(req, dname, proj_type, cmd_func, cmd_args, cmd_opt)
	w.resize(900, 600)
	w.show()
	return w

if __name__ == '__main__':
	import optparse
	usage = "usage: %prog (-d <code_dir/file> | -t <prj_type>) [symbol]"
	op = optparse.OptionParser(usage=usage)
	op.add_option("-d", "--codedir", dest="code_dir", help="Code dir", metavar="CODE_DIR")
	op.add_option("-t", "--type", dest="prj_type", help="project type: idutils|gtags|cscope", metavar="PRJ_TYPE")
	(options, args) = op.parse_args()

	# dname
	if not options.code_dir:
		print >> sys.stderr, 'Specify -d'
		sys.exit(-1)
	dname = options.code_dir
	if not os.path.exists(dname):
		print >> sys.stderr, '"%s": does not exist' %  dname
		sys.exit(-2)
	wdir = dname
	if not os.path.isdir(wdir):
		wdir = os.path.dirname(wdir)

	# sym
	sym = None
	if len(args):
		if len(args) != 1:
			print >> sys.stderr, 'Please specify only one symbol'
			sys.exit(-3)
		sym = args[0]

	# ptype
	ptype = options.prj_type
	if ptype:
		if not sym:
			print >> sys.stderr, '-t option needs sepficfying symbol'
			sys.exit(-4)
		if not os.path.isdir(dname):
			print >> sys.stderr, '-t option needs codedir to be a directory'
			sys.exit(-5)
	pcmd = None
	if ptype and os.path.isdir(dname):
		prj_list = [
			['idutils', 'ID'         ],
			['gtags',   'GRTAGS'     ],
			['cscope',  'cscope.out' ],
			['grep',    ''           ],
		]
		for p in prj_list:
			if p[0] == ptype:
				if not os.path.exists(os.path.join(dname, p[1])):
					print >> sys.stderr, 'Failed to find "%s" in directory "%s"' % (p[1], dname)
					sys.exit(-6)
					
	app = QApplication(sys.argv)
	cmd_args = [
		['CLGRAPH', 'D', 'Derived classes'],
		['CLGRAPH', 'B', 'Base classes']
	]

	w = create_page(sym, dname, ptype, None, cmd_args, None)

	sys.exit(app.exec_())
