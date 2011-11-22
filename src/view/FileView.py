#!/usr/bin/python

import os

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class FileTree(QTabWidget):
	sig_show_file = pyqtSignal(str)
	
	def __init__(self, parent=None):
		QWidget.__init__(self)
		self.listw = QWidget()
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
		self.listw.setLayout(vlay)
		self.addTab(self.listw, "List")

		self.le.textChanged.connect(self.le_textChanged)
		self.le.returnPressed.connect(self.le_returnPressed)
		self.qt.itemActivated.connect(self.foldtv_itemActivated)

		self.foldm = QFileSystemModel()
		self.foldm.setRootPath(QDir.rootPath())
		self.foldtv = QTreeView()
		self.foldtv.setModel(self.foldm)
		header = self.foldtv.header()
		for col in range(header.count()):
			if col > 0:
				self.foldtv.setColumnHidden(col, True)
		self.addTab(self.foldtv, "Tree")
		self.foldtv.activated.connect(self.foldtv_itemActivated)

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
		if self.replaceroot:
			filename = filename.replace("...", self.rootpath)
		self.sig_show_file.emit(filename)

	def foldtv_itemActivated(self):
		list = self.foldtv.selectionModel().selectedIndexes()
		for item in list:
			self.sig_show_file.emit(self.foldm.fileInfo(item).absoluteFilePath())
	
	def keyPressEvent(self, ev):
		if ev.key() in [Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp or Qt.Key_PageDown]:
			self.qt.keyPressEvent(ev)
			return

	def clear(self):
		self.le.clear()
		self.qt.clear()

	def add_files(self, flist):
		self.qt.clear()
		self.replaceroot = False
		self.rootpath = QString(os.path.commonprefix(flist))
		if self.rootpath.size() > 8:
			self.replaceroot = True
		for f in flist:
			if self.replaceroot:
				f =  f.replace(self.rootpath, "...")
			item = QTreeWidgetItem([os.path.basename(f), f])
			self.qt.addTopLevelItem(item)
			#if (self.qt.topLevelItemCount() > 0):
				#self.qt.resizeColumnToContents(0)
				#self.qt.resizeColumnToContents(1)
		self.qt.sortByColumn(0, Qt.AscendingOrder)
		self.foldtv.setRootIndex(self.foldm.index(self.rootpath))
			
