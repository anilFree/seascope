#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import re

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import DialogManager

class ResultPageItem(QTreeWidgetItem):
	def __init__(self, li):
		QTreeWidgetItem.__init__(self, li)
	def column_val(self, col):
		try:
			val = str(self.data(col, Qt.DisplayRole).toString())
		except:
			return None
		return val

class ResultPage(QTreeWidget):
	sig_show_file_line = pyqtSignal(str, int)
	is_history_call = False

	def __init__(self, parent):
		QTreeWidget.__init__(self)

		self.is_history = False
		self.pbar = None
		self.parent = parent

		self.setColumnCount(4)
		self.cmd_items = ['Tag', 'File', 'Line', 'Text'] 
		self.setHeaderLabels(self.cmd_items)
		self.setColumnWidth(0, 200)
		self.setColumnWidth(1, 300)
		self.setColumnWidth(2, 40)

		# setup popup menu
		self.pmenu = QMenu()
		self.pmenu.addAction("&Filter", self.filter_cb)
		self.pmenu.addAction("&Show All", self.show_all_cb)
		self.pmenu.addSeparator()
		self.pmenu.addAction("&Remove Item", self.remove_item_cb)

		#self.setMinimumHeight(200)
		#self.setMinimumWidth(600)


		## set column width to fit contents
		##self.resizeColumnsToContents()
		##self.resizeRowsToContents()

		## set row height
		#nrows = len(result)
		#for row in xrange(nrows):
			#self.setRowHeight(row, 14)

		#self.setTextElideMode(Qt.ElideLeft)
		self.setIndentation(-2)
		self.setAllColumnsShowFocus(True)
		
		self.activated.connect(self.activated_cb)

	def activated_cb(self, minx):
		(filename, line) = self.get_file_line(minx)
		if (not filename):
			return
		if (self.is_history):
			ResultPage.is_history_call = True
		self.sig_show_file_line.emit(filename, line)
		ResultPage.is_history_call = False

	def filter_cb(self):
		filtered = False
		cmd_sel = self.cmd_items[self.last_minx.column()]
		res = DialogManager.show_filter_dialog(self.cmd_items,cmd_sel)
		if res == None:
			return
		(filter_text, is_regex, is_negate, is_ignorecase, cmd_sel) = res
		cmd_idx = self.cmd_items.index(cmd_sel)
		if cmd_idx == -1:
			return
		for inx in range(self.topLevelItemCount()):
			item = self.topLevelItem(inx)
			text = item.column_val(cmd_idx)
			if (text == None):
				continue
			matched = False
			if (is_regex):
				if (is_ignorecase):
					if (re.search(filter_text, text, re.I) != None):
						matched = True
				else:
					if (re.search(filter_text, text) != None):
						matched = True
			else:
				if (is_ignorecase):
					if (text.upper().find(filter_text.upper()) != -1):
						matched = True
				else:
					if (text.find(filter_text) != -1):
						matched = True
			if (is_negate):
				matched = not matched
			if not matched:
				self.setItemHidden(item, True)
				filtered = True
		if filtered:
			self.mark_tab_filtered(True)

	def mark_tab_filtered(self, mark):
		tabIndex = self.parent.indexOf(self)
		label = self.parent.tabText(tabIndex)
		if mark and label[0] != "*":
			self.parent.setTabText(tabIndex, "*" + label)
		elif not mark and label[0] == "*":
			self.parent.setTabText(tabIndex, label.remove(0,1))

	def show_all_cb(self):
		for inx in range(self.topLevelItemCount()):
			item = self.topLevelItem(inx)
			self.setItemHidden(item, False)
		self.mark_tab_filtered(False)

	def remove_item_cb(self):
		self.setItemHidden(self.itemFromIndex(self.last_minx), True)
		self.mark_tab_filtered(True)

	def get_file_line(self, minx):
		model = minx.model()
		row = minx.row()
		if (not model):
			return (None, None)
		filename = str(model.data(model.index(row, 1)).toString())
		try:
			line = model.data(model.index(row, 2)).toString()
			line = int(line)
		except:
			line = 0
		return (filename, line)

	def add_result_continue(self):
		self.add_result(self.name, self.res)

	def add_result(self, name, res):
		res_list = []
		ret_val = True
		root = self.invisibleRootItem()
		count = 0
		for line in res:
			item = ResultPageItem(line)
			#self.addTopLevelItem(item)
			if (self.is_history):
				root.insertChild(0, item)
			else:
				root.addChild(item)
			count = count + 1
			if (count == 1000):
				self.name = name
				self.res = res[count:]
				QTimer.singleShot(100, self.add_result_continue)
				return
		self.remove_progress_bar()
		if (self.topLevelItemCount() < 5000):
			self.resizeColumnToContents(0)
			self.resizeColumnToContents(1)
			self.resizeColumnToContents(2)
			self.resizeColumnToContents(3)
		if (self.topLevelItemCount() == 1):
			item = self.topLevelItem(0)
			item.setSelected(True)
			minx = self.indexFromItem(item)
			self.activated_cb(minx)
		return ret_val

	def mousePressEvent(self, m_ev):
		QTreeWidget.mousePressEvent(self, m_ev)
		if (m_ev.button() == Qt.RightButton):
			self.last_minx = self.indexAt(m_ev.pos())
			self.pmenu.exec_(QCursor.pos())

	def show_progress_bar(self):
		self.pbar = QProgressBar(self)
		self.pbar.setMinimum(0)
		self.pbar.setMaximum(0)
		self.pbar.show()

	def remove_progress_bar(self):
		if (self.pbar):
			self.pbar.setParent(None)
			self.pbar = None

class ResultManager(QTabWidget):
	book = None
	sig_show_file_line = pyqtSignal(str, int)

	def __init__(self, *args):
		apply(QTabWidget.__init__,(self, ) + args)

		self.setMovable(True)
		self.setTabsClosable(True)
		self.tabCloseRequested.connect(self.close_cb)

		self.h_page = None

		self.setFont(QFont("San Serif", 8))
		ResultManager.book = self

	def go_next_res_common(self, page, inc):
		if page == None:
			return
		if (inc == 1):
			minx = page.moveCursor(QAbstractItemView.MoveDown, Qt.NoModifier)
		else:
			minx = page.moveCursor(QAbstractItemView.MoveUp, Qt.NoModifier)
		page.setCurrentItem(page.itemFromIndex(minx))
		page.activated.emit(minx)
	def go_next_res(self, inc):
		self.go_next_res_common(self.currentWidget(), inc)
	def go_next_history(self, inc):
		self.go_next_res_common(self.h_page, -inc)
	def show_history(self):
		if (self.h_page):
			self.setCurrentWidget(self.h_page)

	def new_cb(self):
		print "new_cb"
	def refresh_cb(self):
		print "refresh_cb"
	def close_cb(self, inx):
		if (self.widget(inx) == self.h_page):
			self.h_page = None
		self.removeTab(inx)
	def close_all_cb(self):
		if DialogManager.show_yes_no("Close all query results ?"):
			self.clear()
			self.h_page = None

	def mousePressEvent(self, m_ev):
		QTabWidget.mousePressEvent(self, m_ev)
		if (m_ev.button() == Qt.RightButton):
			# setup popup menu
			self.pmenu = QMenu()
			#self.pmenu.addAction("&New", self.new_cb)
			#self.pmenu.addAction("&Refresh", self.refresh_cb)
			#self.pmenu.addSeparator()
			self.pmenu.addAction("Close &All", self.close_all_cb)
			self.pmenu.exec_(QCursor.pos())

	def history_create(self):
		self.h_page = ResultManager.create_result_page(self, None)
		assert self.h_page.is_history
		self.h_page.hideColumn(0)
		self.h_page.hideColumn(3)
		
	def history_update(self, filename, line):
		if (ResultPage.is_history_call):
			return
		if (self.h_page == None):
			self.history_create()
	
		for idx in range(self.h_page.indexOfTopLevelItem(self.h_page.currentItem())):
			self.h_page.invisibleRootItem().removeChild(self.h_page.topLevelItem(0))

		if self.h_page.topLevelItemCount():
			item = self.h_page.topLevelItem(0)
			minx = self.h_page.indexFromItem(item)
			(f, l) = self.h_page.get_file_line(minx)
			if (filename and f == filename and l == line):
				return
		self.h_page.add_result('History', [['', filename, str(line), '']])
		if self.h_page.topLevelItemCount():
			self.h_page.setCurrentItem(self.h_page.topLevelItem(0))

	def create_result_page(self, name):
		page = ResultPage(self)
		if not name:
			name = 'History'
			page.is_history = True
		self.addTab(page, name)
		if not page.is_history:
			self.setCurrentWidget(page)
		page.sig_show_file_line.connect(self.sig_show_file_line)
		page.show_progress_bar()
		return page

	def create_result_page_single(self):
		return ResultPage(self)
