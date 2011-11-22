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

		self.lview = QTreeWidget(self)
		self.lview.setColumnCount(2)
		self.lview.setHeaderLabels(['File', 'Path'])
		self.lview.setFont(QFont("San Serif", 8))
		self.lview.setIndentation(-2)
		self.lview.setAllColumnsShowFocus(True)

		vlay = QVBoxLayout()
		vlay.addWidget(self.le)
		vlay.addWidget(self.lview)
		self.listw.setLayout(vlay)
		self.addTab(self.listw, "List")

		self.le.textChanged.connect(self.le_textChanged)
		self.le.returnPressed.connect(self.le_returnPressed)
		self.lview.itemActivated.connect(self.lview_itemActivated)

		self.tmodel = QFileSystemModel()
		self.tmodel.setRootPath(QDir.rootPath())
		self.tview = QTreeView()
		self.addTab(self.tview, "Tree")
		self.tview.activated.connect(self.tview_itemActivated)

                self.clear()

	def le_textChanged(self, text):
		if (text == ''):
			return
		self.lview.keyboardSearch('')
		self.lview.keyboardSearch(text)

	def le_returnPressed(self):
		self.le.clear()
		items = self.lview.selectedItems()
		if len(items) == 0:
			return
		self.lview.itemActivated.emit(items[0], 0)

	def lview_itemActivated(self, item):
		filename = str(item.data(1, Qt.DisplayRole).toString())
		if self.is_rel_path:
			filename = filename.replace("...", self.dir_prefix)
		self.sig_show_file.emit(filename)

	def tview_itemActivated(self):
		list = self.tview.selectionModel().selectedIndexes()
		for item in list:
			if self.tmodel.fileInfo(item).isFile():
				self.sig_show_file.emit(self.tmodel.fileInfo(item).absoluteFilePath())
	
	def keyPressEvent(self, ev):
		if ev.key() in [Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp or Qt.Key_PageDown]:
			self.lview.keyPressEvent(ev)
			return

	def search_file_cb(self):
		self.le.setFocus()
		self.setCurrentIndex(0)

	def clear(self):
		self.is_rel_path = False
		self.dir_prefix = None 
		self.le.clear()
		self.lview.clear()
                #self.tview.reset()
                self.tview.setModel(None)

	def add_files(self, flist):
		self.lview.clear()
                self.dir_prefix = os.path.dirname(os.path.commonprefix(flist))
		if len(self.dir_prefix) > 16:
			self.is_rel_path = True
		for f in flist:
			if self.is_rel_path:
				f =  f.replace(self.dir_prefix, "...")
			item = QTreeWidgetItem([os.path.basename(f), f])
			self.lview.addTopLevelItem(item)
			#if (self.lview.topLevelItemCount() > 0):
				#self.lview.resizeColumnToContents(0)
				#self.lview.resizeColumnToContents(1)
		self.lview.sortByColumn(0, Qt.AscendingOrder)

		header = self.tview.header()
                self.tview.setModel(self.tmodel)
		for col in range(header.count()):
			if col > 0:
				self.tview.setColumnHidden(col, True)
		self.tview.setRootIndex(self.tmodel.index(self.dir_prefix))
