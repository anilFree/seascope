#!/usr/bin/python

import os

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class FileTree(QWidget):
	sig_show_file = pyqtSignal(str)
	
	def __init__(self, parent=None):
		QWidget.__init__(self)
		self.le = QLineEdit()

		self.qt = QTreeWidget(self)
		self.qt.setColumnCount(2)
		self.qt.setHeaderLabels(['File', 'Path'])
		self.qt.setFont(QFont("San Serif", 8))
		self.qt.setIndentation(-2)
		self.qt.setAllColumnsShowFocus(True)

		vlay = QVBoxLayout()
		vlay.addWidget(self.le)
		vlay.addWidget(self.qt)
		self.setLayout(vlay)

		self.le.textChanged.connect(self.le_textChanged)
		self.le.returnPressed.connect(self.le_returnPressed)
		self.qt.itemActivated.connect(self.qt_itemActivated)

	def le_textChanged(self, text):
		if (text == ''):
			return
		self.qt.keyboardSearch('')
		self.qt.keyboardSearch(text)

	def le_returnPressed(self):
		self.le.clear()
		items = self.qt.selectedItems()
		if len(items) == 0:
			return
		self.qt.itemActivated.emit(items[0], 0)

	def qt_itemActivated(self, item):
		filename = str(item.data(1, Qt.DisplayRole).toString())
		self.sig_show_file.emit(filename)

	def keyPressEvent(self, ev):
		if ev.key() in [Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp or Qt.Key_PageDown]:
			self.qt.keyPressEvent(ev)
			return

	def clear(self):
		self.le.clear()
		self.qt.clear()

	def add_files(self, flist):
		self.qt.clear()
		for f in flist:
			item = QTreeWidgetItem([os.path.basename(f), f])
			self.qt.addTopLevelItem(item)
			#if (self.qt.topLevelItemCount() > 0):
				#self.qt.resizeColumnToContents(0)
				#self.qt.resizeColumnToContents(1)
		self.qt.sortByColumn(0, Qt.AscendingOrder)
