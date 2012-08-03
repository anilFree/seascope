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

		self.filename = filename

		## Choose a lexer
		if not self.lexer:
			if (re.search('\.(py|pyx|pxd|pxi|scons)$', filename) != None):
				self.lexer = QsciLexerPython()
			else:
				self.lexer = QsciLexerCPP()

		## Braces matching
		self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

		## Render on screen
		self.show()

		## Show this file in the editor
		self.setText(open(filename).read())

		## process for modifiled.
		self.setModified(False)
		self.modificationChanged.connect(self.modifiedChanged)
		
		## support edit 
		self.setReadOnly(False)
		self.show()

		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		self.setFocus()

		

	def modifiedChanged(self):
		self.sig_file_modified.emit(self.isModified())
	
	# FIXME: too simple for big files or remote files.	
	def save_file(self, filename):
		if(self.isModified()):
			fobj = open(filename, 'w')
			if (not fobj.closed):
				fobj.write(str(self.text()))
				fobj.flush()
				fobj.close()
				self.setModified(False)

class EditorPageRW(EditorPage):
	def __init__(self, parent=None):
		QSplitter.__init__(self)
		self.fcv = FileContextView(self)
		self.ev = EditorViewRW(self)
		self.addWidget(self.fcv)
		self.addWidget(self.ev)
		self.setSizes([1, 300])

		self.ev.cursorPositionChanged.connect(self.fcv.sig_ed_cursor_changed)
		self.fcv.sig_goto_line.connect(self.ev.goto_line)	
		

class EditorBookRW(EditorBook):

	
	def addFile(self, filename):
		ed = EditorPageRW()
		ed.open_file(filename)
		ed.ev.show_line_number_cb(self.is_show_line)
		ed.ev.set_font(self.ev_font)
		self.addTab(ed, fileName)

	# save current file
	def save_current_page(self):
		page = self.widget(self.currentIndex())
		filename = page.get_filename()
		if (filename):
			page.ev.save_file(filename)

	def save_all_file(self):
		for i in range(self.count()):
			page = self.widget(i)
			filename = page.get_filename()
			if (filename):
				page.ev.save_file(filename)

	def page_modified_cb(self, isModifiled):
		inx = self.currentIndex()
		filename = self.tabText(inx)
		# Sign modified.
		if isModifiled:
			filename = "*" + filename
			self.setTabText(inx, filename)
		else:
			filename = str(filename)
			filename = filename.strip('*')
			self.setTabText(inx, filename)	
	
	def close_cb(self, inx):
		page = self.widget(self.currentIndex())
		if (page.ev.isModified()):
			if DialogManager.show_yes_no("Do you want to save files ?"):
				self.save_current_page()
		self.removeTab(inx)

	def close_all_cb(self):
		needSave = False
		for i in range(self.count()):
			page = self.widget(i)
			if (page.ev.isModified()):
				needSave = True
				break
		if needSave:
			if DialogManager.show_yes_no("Save all changes ?"):
				self.save_all_file()	
			self.clear()
		else:
			if DialogManager.show_yes_no("Close all files ?"):
				self.clear()


	def show_file_line(self, filename, line):
		if (line != None):
			(f, l) = self.get_current_file_line()
			if (f):
				self.sig_history_update.emit(f, l)
		filename = str(filename)
		if (not os.path.exists(filename)):
			return
		page = self.search_already_opened_files(filename)
		if (page == None):	
			page = EditorPageRW()
			page.open_file(filename)
			page.ev.set_font(self.ev_font)
			page.ev.show_line_number_cb(self.is_show_line)
			self.addTab(page, os.path.basename(filename))

		# modified signal callback
		page.ev.sig_file_modified.connect(self.page_modified_cb)
		
		self.setCurrentWidget(page)
		if (line != None):
			page.ev.goto_line(line)
			self.sig_history_update.emit(filename, line)
		page.ev.setFocus()
		
	# redo editing callback
	def redo_edit_cb(self):
		ed = self.currentWidget()
		if (ed):
			ed.ev.redo()

	# undo editing callback
	def undo_edit_cb(self):
		ed = self.currentWidget()
		if (ed):
			ed.ev.undo()

	# edting callbacks
	def copy_edit_cb(self):
		ed = self.currentWidget()
		if (ed):
			ed.ev.copy()

	def cut_edit_cb(self):
		ed = self.currentWidget()
		if (ed):
			ed.ev.cut()

	def paste_edit_cb(self):
		ed = self.currentWidget()
		if (ed):
			ed.ev.paste()

	
