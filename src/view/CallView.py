#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class CallTreeWidgetItem(QTreeWidgetItem):
	def __init__(self, li):
		QTreeWidgetItem.__init__(self, li)
		func = li[0]
		if (func == "<global>"):
			self.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicatorWhenChildless)
		else:
			self.setChildIndicatorPolicy(QTreeWidgetItem.ShowIndicator)
		self.is_done = False

	def set_no_children(self):
		self.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicatorWhenChildless)

	def column_val(self, col):
		return str(self.data(col, Qt.DisplayRole).toString())

	def add_result(self, res):
		self.is_done = True
		res_list = []
		ret_val = True
		for line in res:
			if (line[0] == "<global>"):
				continue
			if (line[0] == self.column_val(0)):
				if (line [1] == self.column_val(1) and line[2] == self.column_val(2)):
					continue
			self.addChild(CallTreeWidgetItem(line))
		if (self.childCount() == 0):
			self.set_no_children()
		# resize column
		self.treeWidget().resizeColumnToContents(0)
		self.treeWidget().resizeColumnToContents(1)
		self.treeWidget().resizeColumnToContents(2)
		self.treeWidget().resizeColumnToContents(3)
		# hdr
		#self.treeWidget().header().setDefaultAlignment(Qt.AlignRight)
		return ret_val

class CallTreeWidget(QTreeWidget):
	sig_show_file_line = pyqtSignal(str, int)

	def __init__(self, parent, cmd_func, cmd_id, cmd_opt):
		QTreeWidget.__init__(self, parent)
		self.is_busy = False
		self.cmd_func = cmd_func
		self.cmd_id = cmd_id
		self.cmd_opt = cmd_opt
		
		self.itemExpanded.connect(self.ctree_itemExpanded)
		self.itemActivated.connect(self.ctree_itemActivated)

		self.setExpandsOnDoubleClick(False)
		self.setColumnCount(4)
		self.setHeaderLabels(['Tag', 'File', 'Line', 'Text'])

		self.setSelectionMode(QAbstractItemView.SingleSelection)
		#self.resize(QSize(800, 500))
		self.setMinimumWidth(800)
		self.setMinimumHeight(500)

		##sel behaviour
		#self.setSelectionBehavior(QAbstractItemView.SelectRows)
		## set the font
		self.setFont(QFont("San Serif", 8))

		#self.setTextElideMode(Qt.ElideLeft)
		self.setAllColumnsShowFocus(True)

	def add_root(self, name):
		parent = CallTreeWidgetItem([name, '', '', ''])
		self.addTopLevelItem(parent)
		parent.setExpanded(True)

	def mousePressEvent(self, m_ev):
		QTreeWidget.mousePressEvent(self, m_ev)
		if (m_ev.button() == Qt.RightButton):
			self.last_minx = self.indexAt(m_ev.pos())

	def ctree_itemActivated(self, item, col):
		filename = item.column_val(1)
		try:
			line = int(item.column_val(2))
		except:
			return
		self.sig_show_file_line.emit(filename, line)

	def ctree_itemExpanded(self, item):
		if (item.is_done):
			return
		tag = str(item.data(0, Qt.DisplayRole).toString())
		if str(item.data(1, Qt.DisplayRole).toString()) == '':
			opt = self.cmd_opt
		else:
			opt = None
		if (self.is_busy):
			return
		self.is_busy = True
		self.pbar = QProgressBar(self)
		self.pbar.setMinimum(0)
		self.pbar.setMaximum(0)
		self.pbar.show()
		
		## add result
		sig_res = self.cmd_func(self.cmd_id, tag, opt)
		self.query_item = item
		sig_res[0].connect(self.ctree_add_result)

	def ctree_add_result(self, req, res):
		def __relevancy_sort(pfile, res):
			import os, re
			pt = []
			pd = {}
			p = pfile
			(pre, ext) = os.path.splitext(pfile)
			c = None
			while p != c:
				e = [p, [], []]
				pt += [e]
				pd[p] = e
				c = p
				p = os.path.dirname(p)
			for line in res:
				f = line[1]
				d = os.path.dirname(f)
				p = f
				while p not in pd:
					p = os.path.dirname(p)
				e = pd[p]
				if p in [f, d]:
					e[1].append(line)
				else:
					e[2].append(line)
			for e in pt:
				e[1] = sorted(e[1], key=lambda li: li[1])
				e[2] = sorted(e[2], key=lambda li: li[1])
			pre = pre + '.*'
			e0 = []
			e1 = []
			for e in pt[1][1]:
				if re.match(pre, e[1]):
					e0 += [e]
				else:
					e1 += [e]
			pt[0][1] += e0
			pt[1][1] = e1

			res1 = []
			res2 = []
			for e in pt:
				res1 += e[1]
				res2 += e[2]
			res = res1 + res2
			return res
		def relevancy_sort(item, res):
			pfile = str(item.data(1, Qt.DisplayRole).toString())
			if pfile == '':
				return res
			if len(res) > 10000:
				return res
			return __relevancy_sort(pfile, res)
		res = relevancy_sort(self.query_item, res)
		self.query_item.add_result(res)
		self.is_busy = False
		if self.pbar:
			self.pbar.setParent(None)
			self.pbar = None


class CallTreeWindow(QMainWindow):
	sig_show_file_line = pyqtSignal(str, int)
	parent = None

	def __init__(self, req, cmd_func, cmd_args, cmd_opt):
		QMainWindow.__init__(self, CallTreeWindow.parent)
		self.req = req

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

			ct = CallTreeWidget(self, cmd_func, cmd[0], cmd_opt)
			ct.sig_show_file_line.connect(self.sig_show_file_line)
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
		if ct.topLevelItemCount() == 0:
			ct.add_root(self.req)
		ct.setFocus()

def ctree_show_file_line(filename, line):
	parent = CallTreeWindow.parent
	parent.raise_()
	parent.activateWindow()
	parent.show_file_line(filename, line)

def create_page(req, cmd_func, cmd_args, cmd_opt):
	w = CallTreeWindow(req, cmd_func, cmd_args, cmd_opt)
	w.sig_show_file_line.connect(ctree_show_file_line)
	w.show()
