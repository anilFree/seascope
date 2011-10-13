#!/usr/bin/python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from CscopeProject import CsQuery

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

	def __init__(self, parent, cmd_id):
		QTreeWidget.__init__(self, parent)
		self.is_busy = False
		self.cmd_id = cmd_id
		
		self.itemExpanded.connect(self.ctree_itemExpanded)
		self.itemActivated.connect(self.ctree_itemActivated)

		self.setExpandsOnDoubleClick(False)
		self.setColumnCount(4)
		self.setHeaderLabels(['Function', 'File', 'Line', 'Text'])

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
		func = str(item.data(0, Qt.DisplayRole).toString())
		if (self.is_busy):
			return
		self.is_busy = True
		
		## add result
		sig_res = CsQuery.cs_query(self.cmd_id, func)
		self.query_item = item
		sig_res[0].connect(self.ctree_add_result)

	def ctree_add_result(self, req, res):
		self.query_item.add_result(res)
		self.is_busy = False

class CallTreeWindow(QMainWindow):
	sig_show_file_line = pyqtSignal(str, int)

	def __init__(self, parent, req):
		QMainWindow.__init__(self, parent)
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
		
		btn_str = ['--> F', 'F -->', '==> F']
		btn_tip = ['Calling tree', 'Called tree', 'Advanced calling tree']
		cmd_ids = [3, 2, 0]
		self.bgrp = QButtonGroup()
		self.bgrp.buttonClicked.connect(self.set_current)
		self.bgrp.setExclusive(True)

		self.btn = []
		self.ctree = []
		for inx in range(3):
			btn = QToolButton()
			btn.setText(btn_str[inx])
			btn.setToolTip(btn_tip[inx])
			#btn.setFlat(True)
			btn.setCheckable(True)
			self.bgrp.addButton(btn, inx)
			self.hlay.addWidget(btn)

			ct = CallTreeWidget(self, cmd_ids[inx])
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
