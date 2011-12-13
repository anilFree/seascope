#!/usr/bin/python

import os

from PyQt4.QtGui import *
from PyQt4.QtCore import *

class FileTree(QTabWidget):
	sig_show_file = pyqtSignal(str)
	
	def __init__(self, parent=None):
		QWidget.__init__(self)

		# List view
		self.listw = QWidget()
		self.le = QLineEdit()

		self.lview = QTreeWidget(self)
		self.lview.setColumnCount(2)
		self.lview.setHeaderLabels(['File', 'Path'])
		self.lview.setFont(QFont("San Serif", 8))
		self.lview.setIndentation(-2)
		self.lview.setAllColumnsShowFocus(True)

		lvlay = QVBoxLayout()
		lvlay.addWidget(self.le)
		lvlay.addWidget(self.lview)
		self.listw.setLayout(lvlay)
		self.addTab(self.listw, "List")

		self.le.textChanged.connect(self.le_textChanged)
		self.le.returnPressed.connect(self.le_returnPressed)
		self.lview.itemActivated.connect(self.lview_itemActivated)

		# Tree view
		self.treew = QWidget()
		self.tmodel = QFileSystemModel()
		self.tmodel.setRootPath(QDir.rootPath())
		self.tview = QTreeView()
		self.tview.setHeaderHidden(True)

		self.ted = QLineEdit()
		self.completer = QCompleter()
		self.completer.setCompletionMode(QCompleter.PopupCompletion)
		self.ted.setToolTip("Current folder")
		self.ted.setCompleter(self.completer)
		self.tdbtn = QPushButton()
		self.tdbtn.setIcon(QApplication.style().standardIcon(QStyle.SP_DirIcon))
		self.tdbtn.setToolTip("Open folder for browsing")
		self.trbtn = QPushButton()
		self.trbtn.setIcon(QApplication.style().standardIcon(QStyle.SP_BrowserReload))
		self.trbtn.setToolTip("Reset to common top-level folder of file in list")

		self.completer.setModel(self.tmodel)
                self.tview.setModel(self.tmodel)

		thlay = QHBoxLayout()
		thlay.addWidget(self.ted)
		thlay.addWidget(self.tdbtn)
		thlay.addWidget(self.trbtn)
		tvlay = QVBoxLayout()
		tvlay.addLayout(thlay)
		tvlay.addWidget(self.tview)
		self.treew.setLayout(tvlay)
		self.addTab(self.treew, "Tree")

		self.tview.activated.connect(self.tview_itemActivated)
		self.tdbtn.clicked.connect(self.change_btn_cb)
		self.ted.editingFinished.connect(self.ted_editingFinished)
		self.trbtn.clicked.connect(self.reset_btn_cb)

                self.clear()

	def resizeEvent(self, event):
		self.tdbtn.setMaximumHeight(self.ted.height())
		self.trbtn.setMaximumHeight(self.ted.height())
		QTabWidget.resizeEvent(self, event)

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
	
	def ted_editingFinished(self):
		path = str(self.ted.text())
		if not os.path.isdir(path):
			path = os.path.dirname(path)
		if os.path.isdir(path):
			self.dir_reset(path)
		else:
			self.dir_reset(self.dir_prefix)

	def change_btn_cb(self):
		fdlg = QFileDialog(None, "Choose directory to browse")
		fdlg.setFileMode(QFileDialog.Directory)
		fdlg.setOptions(QFileDialog.ShowDirsOnly) # and QFileDialog.HideNameFilterDetails)
		fdlg.setDirectory(self.ted.text())
		if (fdlg.exec_()):
			browse_dir = fdlg.selectedFiles()[0]
			self.dir_reset(str(browse_dir))

	def reset_btn_cb(self):
		self.dir_reset(self.dir_prefix)
		
	def dir_reset(self, dirstr):
		self.tview.setRootIndex(self.tmodel.index(dirstr))
		self.ted.setText(dirstr)

	def keyPressEvent(self, ev):
		if ev.key() in [Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp or Qt.Key_PageDown]:
			self.lview.keyPressEvent(ev)
			return

	def search_file_cb(self):
		self.le.setFocus()
		self.le.selectAll()
		self.setCurrentIndex(0)

	def clear(self):
		self.is_rel_path = False
		self.dir_prefix = QDir.rootPath() 
		self.le.clear()
		self.lview.clear()
                self.dir_reset(self.dir_prefix)

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

		self.hide_view_columns(self.tview)
		self.dir_reset(self.dir_prefix)

	def hide_view_columns(self, view):
		header = view.header()
		for col in range(header.count()):
			if col > 0:
				view.setColumnHidden(col, True)
