#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os

from PyQt4.QtGui import *
from PyQt4.QtCore import *

dir_prefix = None

class DirTab(QWidget):
	sig_show_file = pyqtSignal(str)

	def __init__(self, parent=None):
		QWidget.__init__(self)

		self.is_ft = False
		self.d = None

		# Tree view
		self.tmodel = QFileSystemModel()
		self.tmodel.directoryLoaded.connect(self.tmodel_dir_loaded)
		self.tmodel.setRootPath(QDir.rootPath())
		self.tview = QTreeView()
		self.tview.setHeaderHidden(True)
		# For proper horizaontal scroll bar
		self.tview.setTextElideMode(Qt.ElideNone)
		self.tview.expanded.connect(self.tview_expanded_or_collapsed)
		self.tview.collapsed.connect(self.tview_expanded_or_collapsed)

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
		
		self.setLayout(tvlay)

		self.tview.activated.connect(self.tview_itemActivated)
		self.tdbtn.clicked.connect(self.change_btn_cb)
		self.ted.editingFinished.connect(self.ted_editingFinished)
		self.trbtn.clicked.connect(self.reset_btn_cb)

		self.hide_view_columns(self.tview)

	def tmodel_dir_loaded(self, path):
		self.tview.resizeColumnToContents(0)

	def tview_expanded_or_collapsed(self, inx):
		self.tview.resizeColumnToContents(0)

	def dir_name(self):
		return self.d

	def hide_view_columns(self, view):
		header = view.header()
		for col in range(header.count()):
			if col > 0:
				view.setColumnHidden(col, True)


	def tview_itemActivated(self):
		list = self.tview.selectionModel().selectedIndexes()
		for item in list:
			if self.tmodel.fileInfo(item).isFile():
				self.sig_show_file.emit(self.tmodel.fileInfo(item).absoluteFilePath())
	
	def set_tab_name(self, dirstr):
		# Set tab name
		inx = self.parent.indexOf(self)
		try:
			if dirstr != dir_prefix:
				name = os.path.split(dirstr)[1]
			else:
				name = ''
			self.parent.setTabText(inx, name)
		except:
			pass

	def dir_reset(self, dirstr):
		self.set_tab_name(dirstr)
		self.d = dirstr
		self.tview.setRootIndex(self.tmodel.index(dirstr))
		self.ted.setText(dirstr)
		
	def ted_editingFinished(self):
		path = str(self.ted.text())
		if not os.path.isdir(path):
			path = os.path.dirname(path)
		if os.path.isdir(path):
			self.dir_reset(path)
		else:
			self.dir_reset(dir_prefix)

	def change_btn_cb(self):
		fdlg = QFileDialog(None, "Choose directory to browse")
		fdlg.setFileMode(QFileDialog.Directory)
		fdlg.setOptions(QFileDialog.ShowDirsOnly) # and QFileDialog.HideNameFilterDetails)
		fdlg.setDirectory(self.ted.text())
		if (fdlg.exec_()):
			browse_dir = fdlg.selectedFiles()[0]
			self.dir_reset(str(browse_dir))

	def reset_btn_cb(self):
		self.dir_reset(dir_prefix)

	def resizeEvent(self, event):
		self.tdbtn.setMaximumHeight(self.ted.height())
		self.trbtn.setMaximumHeight(self.ted.height())

class FileTab(QWidget):
	sig_show_file = pyqtSignal(str)
	
	def __init__(self, parent=None):
		QWidget.__init__(self)

		self.is_ft = True

		# List view
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
		self.setLayout(lvlay)

		self.le.textChanged.connect(self.le_textChanged)
		self.le.returnPressed.connect(self.le_returnPressed)
		self.lview.itemActivated.connect(self.lview_itemActivated)

		global dir_prefix
		dir_prefix = QDir.rootPath() 

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
			filename = filename.replace("...", dir_prefix, 1)
		self.sig_show_file.emit(filename)

	def keyPressEvent(self, ev):
		if ev.key() in [Qt.Key_Up, Qt.Key_Down, Qt.Key_PageUp or Qt.Key_PageDown]:
			self.lview.keyPressEvent(ev)
			return

	def search_file_cb(self):
		self.le.setFocus()
		self.le.selectAll()

	def clear(self):
		global dir_prefix
		dir_prefix = QDir.rootPath() 
		self.is_rel_path = False
		self.le.clear()
		self.lview.clear()

	def add_files(self, flist):
		global dir_prefix
		self.clear()
		dir_prefix = os.path.dirname(os.path.commonprefix(flist))
		if len(dir_prefix) > 16:
			self.is_rel_path = True
		for f in flist:
			if self.is_rel_path:
				f =  f.replace(dir_prefix, "...", 1)
			item = QTreeWidgetItem([os.path.basename(f), f])
			self.lview.addTopLevelItem(item)
			#if (self.lview.topLevelItemCount() > 0):
				#self.lview.resizeColumnToContents(0)
				#self.lview.resizeColumnToContents(1)
		self.lview.sortByColumn(0, Qt.AscendingOrder)
		self.lview.resizeColumnToContents(0)

class FileTree(QTabWidget):
	sig_show_file = pyqtSignal(str)
	
	def __init__(self, parent=None):
		QTabWidget.__init__(self)
		
		self.setMovable(True)

		t = FileTab()
		icon = QApplication.style().standardIcon(QStyle.SP_FileDialogDetailedView)
		self.addTab(t, icon, '')
		self.ft = t

		self.dlist = []

		self.new_dir_tab_cb()

		self.clear()

		# setup popup menu
		self.pmenu = QMenu()
		self.pmenu.addAction("&New Dir View", self.new_dir_tab_cb)
		self.pmenu.addAction("&Close Active Dir View", self.close_active_dir_tab_cb)
		self.pmenu.addAction("&Close All Dir View", self.close_all_dir_tab_cb)

	def set_tab_dir(self, t, d):
		if d == None or d == dir_prefix:
			t.reset_btn_cb()
		else:
			t.dir_reset(d)

	def new_dir_tab_cb(self, d=None):
		t = DirTab()
		t.parent = self
		self.dlist.append(t)
		icon = QApplication.style().standardIcon(QStyle.SP_DirClosedIcon)
		self.addTab(t, icon, '')
		self.set_tab_dir(t, d)

	def close_all_dir_tab_cb(self):
		for t in self.dlist:
			inx = self.indexOf(t)
			self.removeTab(inx)
		self.dlist = []
		# Always have atleast one dir view
		self.new_dir_tab_cb()

	def get_dir_view_list(self):
		dv_list = []
		for t in self.dlist:
			d = t.dir_name()
			if d != dir_prefix:
				dv_list.append(d)
		return dv_list

	def open_dir_view(self, filename):
		d = filename
		if not os.path.isdir(filename):
			d = os.path.dirname(str(filename))
		self.new_dir_tab_cb(d)

	def close_active_dir_tab_cb(self):
		inx = self.currentIndex()
		if inx < 0:
			return
		t = self.widget(inx)
		if t.is_ft:
			return
		if self.count() <= 2:
			self.close_all_dir_tab_cb()
			return
		self.dlist.remove(t)
		self.removeTab(inx)

	def addTab(self, t, icon, x):
		t.sig_show_file.connect(self.sig_show_file)
		QTabWidget.addTab(self, t, icon, x)
		if self.count() > 2:
			inx = self.indexOf(t)
		else:
			inx = 0
		self.setCurrentIndex(inx)

	def mousePressEvent(self, m_ev):
		QTabWidget.mousePressEvent(self, m_ev)
		if (m_ev.button() == Qt.RightButton):
			self.pmenu.exec_(QCursor.pos())

	def search_file_cb(self):
		self.ft.search_file_cb()
		self.setCurrentWidget(self.ft)

	def clear(self):
		self.ft.clear()
		self.close_all_dir_tab_cb()

	def add_files(self, flist):
		old_dir_prefix = dir_prefix
		self.ft.add_files(flist)
		for t in self.dlist:
			d = t.dir_name()
			if d == old_dir_prefix:
				d = dir_prefix
			self.set_tab_dir(t, d)
