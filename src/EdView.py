#!/usr/bin/env python

import os

from PyQt4 import QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4.Qsci import QsciScintilla, QsciScintillaBase, QsciLexerCPP

import DialogManager
from CtagsView import *

class EditorView(QsciScintilla):
	ev_popup = None
	def __init__(self, parent=None):
		QsciScintilla.__init__(self, parent)
		#self.setGeometry(300, 300, 400, 300)

		## Editing line color
		self.setCaretLineVisible(True)
		self.setCaretLineBackgroundColor(QtGui.QColor("#EEF6FF"))
		#self.setCaretWidth(2)

		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

	def get_filename(self):
		return self.filename

	def ed_settings_1(self):
		## Margins colors
		# line numbers margin
		self.setMarginsBackgroundColor(QtGui.QColor("#333333"))
		self.setMarginsForegroundColor(QtGui.QColor("#CCCCCC"))

		# folding margin colors (foreground,background)
		self.setFoldMarginColors(QtGui.QColor("#99CC66"),QtGui.QColor("#333300"))
		
		## Edge Mode shows a red vetical bar at 80 chars
		self.setEdgeMode(QsciScintilla.EdgeLine)
		self.setEdgeColumn(80)
		self.setEdgeColor(QtGui.QColor("#FF0000"))

		## Editing line color
		self.setCaretLineVisible(True)
		self.setCaretLineBackgroundColor(QtGui.QColor("#CDA869"))

		## Folding visual : we will use boxes
		self.setFolding(QsciScintilla.BoxedTreeFoldStyle)

	def show_line_number_cb(self, val):
		if (val):
			width = self.fm.width( "00000" ) + 5
		else:
			width = 0
		self.setMarginWidth(0, width)
		self.setMarginLineNumbers(0, val)

	def open_file(self, filename):
		self.filename = filename

		## define the font to use
		self.font = QtGui.QFont()
		self.font.setFamily("Monospace")
		self.font.setFixedPitch(True)
		self.font.setPointSize(8)
		# the font metrics here will help
		# building the margin width later
		self.fm = QtGui.QFontMetrics(self.font)

		## set the default font of the editor
		## and take the same font for line numbers
		self.setFont(self.font)
		self.setMarginsFont(self.font)

		## Braces matching
		self.setBraceMatching(QsciScintilla.SloppyBraceMatch)


		## Choose a lexer
		self.lexer = QsciLexerCPP()
		self.lexer.setDefaultFont(self.font)
		self.setLexer(self.lexer)

		## Render on screen
		self.show()

		## Show this file in the editor
		self.setText(open(filename).read())
		
		## Mark read-only
		self.setReadOnly(True)
		self.show()

		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		#self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setFocus()

	def goto_line(self, line):
		line = line - 1
		self.setCursorPosition(line, 0)

		self.ensureLineVisible(line)
		self.setFocus()

	def contextMenuEvent(self, ev):
		EditorView.ev_popup.exec_(QCursor.pos())

class EditorPage(QSplitter):
	def __init__(self, parent=None):
		QSplitter.__init__(self)
		self.cv = CtagsView(self)
		self.ev = EditorView(self)
		self.addWidget(self.cv)
		self.addWidget(self.ev)
		self.setSizes([1, 300])

		self.ev.cursorPositionChanged.connect(self.cv.ct.ed_cursor_changed)
		self.cv.sig_goto_line.connect(self.ev.goto_line)

	def open_file(self, filename):
		self.ev.open_file(filename);
		self.cv.ct.add_ct_result(filename);

	def get_filename(self):
		return self.ev.get_filename()
		
class EditorBook(QTabWidget):
	sig_history_update = pyqtSignal(str, int)
	sig_tab_changed = pyqtSignal(str)

	def __init__(self, *args):
		apply(QTabWidget.__init__,(self, ) + args)

		self.setMovable(True)
		self.setTabsClosable(True)
		self.tabCloseRequested.connect(self.close_cb)
		self.currentChanged.connect(self.tab_change_cb)
		
		self.is_show_line = False
		self.f_text = None

	def addFile(self, fileName):
		ed = EditorPage()
		ed.open_file(fileName)
		ed.ev.show_line_number_cb(self.is_show_line)
		self.addTab(ed, fileName)

	def get_current_word(self):
		ed = self.currentWidget()
		if not ed:
			return
		if ed.ev.hasSelectedText():
			return ed.ev.selectedText()
		(line, index) = ed.ev.getCursorPosition()
		text = ed.ev.text(line)
		# Go left
		linx = index
		while linx > 0 and ed.ev.isWordCharacter(text[linx - 1]):
			linx = linx - 1
		# Go right
		rinx = index
		while rinx < len(text) and ed.ev.isWordCharacter(text[rinx]):
			rinx = rinx + 1
		
		text = text[linx:rinx]
		if text == '':
			return None
		return text
	def get_current_file_line(self):
		ed = self.currentWidget()
		if not ed:
			return (None, None)
		(line, inx) = ed.ev.getCursorPosition()
		return (ed.ev.filename, line + 1)
	def matching_brace_cb(self):
		ed = self.currentWidget()
		if ed:
			ed.ev.moveToMatchingBrace()
			#ed.ev.setFocus()
	def goto_line_cb(self):
		ed = self.currentWidget()
		if not ed:
			return (None, None)
		(line, inx) = ed.ev.getCursorPosition()
		#return (line + 1, ed.ev.lines())
		line = DialogManager.show_goto_line_dialog(line + 1, ed.ev.lines())
		if (line == None):
			return
		ed.ev.goto_line(line)	

	def show_file(self, filename, line):
		for i in range(self.count()):
			ed = self.widget(i)
			if (ed.get_filename() == filename):
				self.setCurrentWidget(ed)
				return
		self.addFile(filename)

	def focus_editor(self):
		page = self.currentWidget()
		if page:
			page.ev.setFocus()

	def close_current_page(self):
		self.removeTab(self.currentIndex())
		self.focus_editor()

	def focus_search_ctags(self):
		ed = self.currentWidget()
		ed.cv.le.setFocus()
		
	def close_cb(self, inx):
		self.removeTab(inx)
	def close_all_cb(self):
		if DialogManager.show_yes_no("Close all files ?"):
			self.clear()
	def tab_change_cb(self, inx):
		if (inx == -1):
			fname = ''
		else:
			fname = self.currentWidget().get_filename()
		self.sig_tab_changed.emit(fname)
			

	def mousePressEvent(self, m_ev):
		QTabWidget.mousePressEvent(self, m_ev)
		if (m_ev.button() == Qt.RightButton):
			# setup popup menu
			self.pmenu = QMenu()
			self.pmenu.addAction("Close &All", self.close_all_cb)
			self.pmenu.exec_(QCursor.pos())

	def search_already_opened_files(self, filename):
		for i in range(self.count()):
			page = self.widget(i)
			if (page.get_filename() == filename):
				return page
		return None

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
			page = EditorPage()
			page.open_file(filename)
			page.ev.show_line_number_cb(self.is_show_line)
			self.addTab(page, os.path.basename(filename))
		
		self.setCurrentWidget(page)
		if (line != None):
			page.ev.goto_line(line)
			self.sig_history_update.emit(filename, line)
		page.ev.setFocus()

	def show_file(self, filename):
		self.show_file_line(filename, None)

	def find_cb(self):
		ed = self.currentWidget()
		if not ed:
			return
		res = DialogManager.show_find_dialog(self.get_current_word())
		if (res == None):
			return
		(text, opt) = res
		if (text == None):
			return
		self.f_text = text
		self.f_opt = opt
		self.find_text(opt['cursor'], opt['fw'])

	def find_text(self, from_cursor, is_fw):
		if (self.f_text == None):
			return
		ed = self.currentWidget()
		if not ed:
			return
		text = self.f_text
		opt = self.f_opt
		if (from_cursor):
			if (is_fw):
				(line, inx) = (-1, -1)
			else:
				(line, inx) = ed.ev.getCursorPosition()
				if (ed.ev.hasSelectedText()):
					inx = inx - 1
			if ed.ev.findFirst(text, opt['re'], opt['cs'], opt['wo'], False, is_fw, line, inx):
				return True
			if not DialogManager.show_yes_no('End of document reached. Continue from beginning?'):
				return False
		if (is_fw):
			(line, inx) = (0, 0)
		else:
			(line, inx) = (ed.ev.lines(), 0)
		if ed.ev.findFirst(text, opt['re'], opt['cs'], opt['wo'], False, is_fw, line, inx):
			return
		DialogManager.show_msg_dialog("Could not find " + "'" + text + "'")

	def find_next_cb(self):
		self.find_text(True, True)

	def find_prev_cb(self):
		self.find_text(True, False)

	def show_line_number_cb(self):
		val = self.m_show_line_num.isChecked()
		self.is_show_line = val
		for inx in range(self.count()):
			ed = self.widget(inx)
			ed.ev.show_line_number_cb(val)

	def open_in_external_editor(self, cmd):
		if not cmd:
			DialogManager.show_msg_dialog('Please configure external editor')
			return
		(f, l) = self.get_current_file_line()
		if not f:
			return
		cmd = cmd.replace('%F', f).replace('%L', str(l))
		if not QProcess.startDetached(cmd):
			DialogManager.show_msg_dialog('Failed to start: ' + cmd)
