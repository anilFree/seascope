#!/usr/bin/python

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import CtagsManager

class CtagsTreeItem(QTreeWidgetItem):
	def __init__(self, li):
		QTreeWidgetItem.__init__(self, li)
		if li[2] in [ 'type', 'struct', 'class', 'enum' ]:
			f = self.font(0)
			f.setBold(True)
			self.setFont(0, f)
			
	def column_val(self, col):
		return str(self.data(col, Qt.DisplayRole).toString())
	def line_val(self):
		return (int(self.column_val(1)))

class CtagsTree(QTreeWidget):
	def __init__(self, parent=None):
		QTreeWidget.__init__(self)
		
		self.setColumnCount(3)
		self.setHeaderLabels(['Name', 'Line', 'Type'])

		#self.setMinimumHeight(200)
		self.setMinimumWidth(50)

		self.setFont(QFont("San Serif", 8))
		
		self.setIndentation(-2)
		self.setAllColumnsShowFocus(True)

	def add_ct_result(self, filename):
		res = CtagsManager.ct_query(filename)
		for line in res:
			item = CtagsTreeItem(line)
			self.addTopLevelItem(item)
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


class CtagsView(QWidget):
	sig_goto_line = pyqtSignal(int)

	def __init__(self, parent=None):
		QWidget.__init__(self)
		self.le = QLineEdit()
		self.ct = CtagsTree(self)
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
