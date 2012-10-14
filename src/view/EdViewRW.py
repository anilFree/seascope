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

	# save current file
	def save_current_page(self):
		page = self.widget(self.currentIndex())
		filename = page.get_filename()
		if (filename):
			page.ev.save_file(filename)
			page.fcv.rerun(filename)

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
		EditorBook.show_file_line(self, filename, line)
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

	
