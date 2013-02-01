#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import CtagsManager

# Search Result
class SR:
	NONE  = 0
	LSKIP = 1
	LUPD  = 2
	MATCH = 3
	RUPD  = 4
	RSKIP = 5
	def __init__(self, k):
		self.line = k
		self.left = 0
		self.right = 1000000
		self.item = None
		self.done = False

class CtagsListItem(QTreeWidgetItem):
	def __init__(self, li):
		QTreeWidgetItem.__init__(self, li)
		if li[2] in [ 'class', 'interface', 'struct', 'type', 'enum', 'constrainer', '' ]:
			self.set_bold()
		if li[2] in [ 'reactor' ]:
			brush = self.foreground(0)
			brush.setColor(Qt.gray)
			self.setForeground(0, brush)

	def set_bold(self):
		f = self.font(0)
		f.setBold(True)
		self.setFont(0, f)
	def column_val(self, col):
		return str(self.data(col, Qt.DisplayRole).toString())
	def line_val(self):
		return (int(self.column_val(1)))

class CtagsList(QTreeWidget):
	def __init__(self, parent=None, isTree=False):
		QTreeWidget.__init__(self)
		
		self.setColumnCount(3)
		self.setHeaderLabels(['Name', 'Line', 'Type'])

		#self.setMinimumHeight(200)
		self.setMinimumWidth(50)

		self.setFont(QFont("San Serif", 8))
		
		if isTree:
			self.setIndentation(12)
			self.setExpandsOnDoubleClick(False)
			#self.setAnimated(True)
		else:
			self.setIndentation(-2)

		self.setAllColumnsShowFocus(True)

	def add_ct_result(self, res):
		for line in res:
			item = CtagsListItem(line)
			self.addTopLevelItem(item)
		#self.sortItems(1, Qt.AscendingOrder)
		#self.resizeColumnsToContents(1)
		self.resizeColumnToContents(0)
		self.resizeColumnToContents(1)
		self.resizeColumnToContents(2)

	def recurseTreeAdd(self, t, p):
		for k, v in t.items():
			if k == '+':
				continue
			if k == '*':
				for line in v:
					item = CtagsListItem(line)
					p.addChild(item)
				continue
			if '+' in v:
				item = CtagsListItem(v['+'])
			else:
				item = CtagsListItem([k, '', '', ''])
			p.addChild(item)
			self.recurseTreeAdd(v, item)
		self.setItemExpanded(p, True)

	def add_ctree_result(self, res):
		p = self.invisibleRootItem()
		self.recurseTreeAdd(res, p)

		#self.sortItems(1, Qt.AscendingOrder)
		#self.resizeColumnsToContents(1)
		self.resizeColumnToContents(0)
		self.resizeColumnToContents(1)
		self.resizeColumnToContents(2)

	def ed_cursor_changed(self, line, pos):
		line = line + 1
		item = self.currentItem()
		if not item:
			item = self.topLevelItem(0)
			if not item:
				return
		if (item.line_val() == line):
			pass
		elif (item.line_val() < line):
			while True:
				next_item = self.itemBelow(item)
				if not next_item:
					break
				if (next_item.line_val() > line):
					break
				item = next_item
		else:
			while True:
				prev_item = self.itemAbove(item)
				if not prev_item:
					break
				item = prev_item
				if (item.line_val() <= line):
					break
		self.setCurrentItem(item)

	def search_item_check(self, item, sr):
		try:
			val = item.line_val()
		except:
			return SR.NONE
		if val < sr.left:
			return SR.LSKIP
		if val < sr.line:
			sr.left = val
			sr.item = item
			return SR.LUPD
		if val == sr.line:
			sr.left = val
			sr.item = item
			sr.done = True
			return SR.MATCH
		if val < sr.right:
			sr.right = val
                        if not sr.item:
				sr.item = item
			return SR.RUPD
		return SR.RSKIP

	def search_recursive(self, p, sr):
		inx = 0;
		r = SR.NONE
		while inx < p.childCount():
			item = p.child(inx)
			if not item.childCount():
				break
			inx += 1
			if r < SR.MATCH:
				r = self.search_item_check(item, sr)
				if r == SR.MATCH:
					return
			self.search_recursive(item, sr)
			if sr.done:
				return
		if not inx < p.childCount():
			return

		last_item = p.child(p.childCount() - 1)
		r = self.search_item_check(last_item, sr)
		if r <= sr.MATCH:
			return

		r = SR.NONE
		while inx < p.childCount():
			item = p.child(inx)
			inx += 1
			r = self.search_item_check(item, sr)
			if r >= SR.MATCH:
				return

	def search_tree(self, line, pos):
		line = line + 1
		sr = SR(line)
		p = self.invisibleRootItem()
		self.search_recursive(p, sr)
		self.setCurrentItem(sr.item)
		

class CtagsListPage(QWidget):
	sig_goto_line = pyqtSignal(int)

	def __init__(self, parent=None):
		QWidget.__init__(self)
		self.le = QLineEdit()
		self.ct = CtagsList(self)
		vlay = QVBoxLayout()
		vlay.addWidget(self.le)
		vlay.addWidget(self.ct)
		self.setLayout(vlay)

		self.le.textChanged.connect(self.le_textChanged)
		self.le.returnPressed.connect(self.le_returnPressed)
		self.ct.itemActivated.connect(self.ct_itemActivated)

	def le_textChanged(self, text):
		#if (len(str(text)) == 1):
			#self.ct.keyboardSearch('')
		self.ct.keyboardSearch('')
		self.ct.keyboardSearch(text)

	def le_returnPressed(self):
		items = self.ct.selectedItems()
		if len(items) == 0:
			return
		self.ct.itemActivated.emit(items[0], 0)

	def ct_itemActivated(self, item):
		try:
			line = int(str(item.data(1, Qt.DisplayRole).toString()))
		except:
			return
		self.sig_goto_line.emit(line)
		self.le.clear()

	def keyPressEvent(self, ev):
		if ev.key() in [Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp or Qt.Key_PageDown]:
			self.ct.keyPressEvent(ev)
			return

	@staticmethod
	def do_ct_query(filename, parent):
		page = CtagsListPage(parent)
		res = CtagsManager.ct_query(filename)
		page.ct.add_ct_result(res)
		parent.add_page(page, 'C')
		parent.sig_ed_cursor_changed.connect(page.ct.ed_cursor_changed)

class CtagsTreePage(QWidget):
	sig_goto_line = pyqtSignal(int)

	def __init__(self, parent=None):
		QWidget.__init__(self)
		self.ct = CtagsList(self, isTree=True)
		vlay = QVBoxLayout()
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
	def do_ct_query(filename, parent):
		(res, isTree) = CtagsManager.ct_tree_query(filename)
		if not isTree:
			return
		page = CtagsTreePage(parent)
		page.ct.add_ctree_result(res)
		parent.add_page(page, 'T')
		parent.sig_ed_cursor_changed.connect(page.ct.search_tree)

def run(filename, parent):
	CtagsListPage.do_ct_query(filename, parent)
	CtagsTreePage.do_ct_query(filename, parent)
