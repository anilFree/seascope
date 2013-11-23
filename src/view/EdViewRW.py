#!/usr/bin/env python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os
import re

from PyQt4 import QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from EdView import *

# inherit from EditView, add editing support.
class EditorViewRW(EditorView):
	sig_file_modified = pyqtSignal(bool)
	def __init__(self, parent=None):
		EditorView.__init__(self, parent)
		# use default settings.
		EditorView.ed_settings_1(self)

	def open_file(self, filename):
		self.open_file_begin(filename)

		## Show this file in the editor
		data = open(filename).read()
		try:
			data = data.decode("UTF-8")
		except:
			pass
		self.setText(data)

		## process for modifiled.
		self.setModified(False)
		self.modificationChanged.connect(self.modifiedChanged)
		
		## support edit 
		self.setReadOnly(False)

		self.open_file_end()

	def refresh_file(self, filename):
		if self.isModified():
			msg = 'Save changes before refresh ?'
			if DialogManager.show_yes_no(msg):
				self.save_file(self.filename)
		EditorView.refresh_file(self, filename)

	def modifiedChanged(self):
		self.sig_file_modified.emit(self.isModified())
	
	# FIXME: too simple for big files or remote files.	
	def save_file(self, filename):
		if(self.isModified()):
			fobj = open(filename, 'w')
			if (not fobj.closed):
				fobj.write(str(self.text().toUtf8()))
				fobj.flush()
				fobj.close()
				self.setModified(False)

class EditorPageRW(EditorPage):
	def new_editor_view(self):
		return EditorViewRW(self)


class EditorBookRW(EditorBook):

	def new_editor_page(self):
		return EditorPageRW()

	def save_file_at_inx(self, inx):
		if inx < 0:
			return
		page = self.widget(inx)
		filename = page.get_filename()
		if filename:
			page.ev.save_file(filename)
			page.fcv.rerun(filename)

	def save_current_page(self):
		inx = self.currentIndex()
		self.save_file_at_inx(inx)

	def save_tab_list(self, inx_list):
		for inx in inx_list:
			self.save_file_at_inx(inx)

	def save_all_file(self):
		inx_list = range(self.count())
		self.save_tab_list(inx_list)

	def page_modified_cb(self, isModifiled):
		inx = self.currentIndex()
		filename = self.tabText(inx)
		# Sign modified.
		if isModifiled:
			self.tabBar().setTabTextColor(inx, Qt.red)
		else:
			self.tabBar().setTabTextColor(inx, Qt.black)
	
	def close_cb(self, inx):
		page = self.widget(self.currentIndex())
		if page.ev.isModified():
			if DialogManager.show_yes_no("Do you want to save file ?"):
				self.save_current_page()
		self.removeTab(inx)

	def has_modified_file(self, inx_list):
		for i in inx_list:
			page = self.widget(i)
			if page.ev.isModified():
				return True
		return False

	def close_list_common(self, type):
		inx_list = self.tab_list(self.currentIndex(), type)
		if len(inx_list) == 0:
			return
		if self.has_modified_file(inx_list):
			msg = 'Closing all %s.\nSave changes ?' % type
			if DialogManager.show_yes_no(msg):
				self.save_tab_list()
			self.remove_tab_list(inx_list)
		else:
			msg = 'Close all %s ?' % type
			if not DialogManager.show_yes_no(msg):
				return
			self.remove_tab_list(inx_list)

	def show_file_line(self, filename, line, hist=True):
		EditorBook.show_file_line(self, filename, line, hist=hist)
		page = self.currentWidget()
		# modified signal callback
		page.ev.sig_file_modified.connect(self.page_modified_cb)
		
	# redo editing callback
	def redo_edit_cb(self):
		ed = self.currentWidget()
		if ed:
			ed.ev.redo()

	# undo editing callback
	def undo_edit_cb(self):
		ed = self.currentWidget()
		if ed:
			ed.ev.undo()

	# edting callbacks
	def cut_edit_cb(self):
		ed = self.currentWidget()
		if ed:
			ed.ev.cut()

	def paste_edit_cb(self):
		ed = self.currentWidget()
		if ed:
			ed.ev.paste()

	
