#!/usr/bin/env python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os
import re
import array

from PyQt4 import QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

try:
	from PyQt4.Qsci import QsciScintilla, QsciScintillaBase
	from PyQt4.Qsci import QsciLexerCPP, QsciLexerJava
	from PyQt4.Qsci import QsciLexerPython, QsciLexerRuby
	from PyQt4.Qsci import QsciLexerBash, QsciLexerDiff, QsciLexerMakefile
	from PyQt4.Qsci import QsciLexerLua, QsciLexerSQL, QsciLexerTCL, QsciLexerTeX
	from PyQt4.Qsci import QsciLexerHTML, QsciLexerCSS
	from PyQt4.Qsci import QsciLexerPerl, QsciLexerVHDL

	suffix_to_lexer = [
		[['c', 'h', 'cpp', 'hpp', 'cc', 'hh', 'cxx', 'hxx', 'C', 'H', 'h++'], QsciLexerCPP],
		[['java'], QsciLexerJava],
		[['py', 'pyx', 'pxd', 'pxi', 'scons'], QsciLexerPython],
		[['rb', 'ruby'], QsciLexerRuby],
		[['sh', 'bash'], QsciLexerBash],
		[['diff', 'patch'], QsciLexerDiff],
		[['mak', 'mk'], QsciLexerMakefile],
		[['lua'], QsciLexerLua],
		[['sql'], QsciLexerSQL],
		[['tcl', 'tk', 'wish', 'itcl'], QsciLexerTCL],
		[['tex'], QsciLexerTeX],
		[['htm', 'html'], QsciLexerHTML],
		[['css'], QsciLexerCSS],
		[['pl', 'perl'], QsciLexerPerl],
		[['vhdl', 'vhd'], QsciLexerVHDL],
	]
	filename_to_lexer = [
		[['Makefile', 'makefile', 'Makefile.am', 'makefile.am', 'Makefile.in', 'makefile.in'], QsciLexerMakefile],
	]

	seascope_editor_tab_width = None
	try:
		seascope_editor_tab_width = int(os.getenv('SEASCOPE_EDITOR_TAB_WIDTH'))
	except:
		pass

except ImportError as e:
	print e
	print "Error: required qscintilla-python package not found"
	raise ImportError

import DialogManager
from FileContextView import *

class EditorViewBase(QsciScintilla):
	def __init__(self, parent=None):
		QsciScintilla.__init__(self, parent)
		self.font = None
		self.lexer = None

	def set_font(self, font):
		if not font:
			return
		if not self.font:
			self.font = QtGui.QFont()
		self.font.fromString(font)

		# the font metrics here will help
		# building the margin width later
		self.fm = QtGui.QFontMetrics(self.font)

		## set the default font of the editor
		## and take the same font for line numbers
		self.setFont(self.font)
		self.setMarginsFont(self.font)

		self.lexer.setFont(self.font,-1)
		self.setLexer(self.lexer)

	def lpropChanged(self, prop, val):
		print 'lpropChanged', prop, val

	def setProperty(self, name, val):
		name_buff = array.array('c', name + "\0")
		val_buff = array.array("c", str(val) + "\0")
		address_name_buffer = name_buff.buffer_info()[0]
		address_val_buffer = val_buff.buffer_info()[0]
		self.SendScintilla(QsciScintillaBase.SCI_SETPROPERTY, address_name_buffer, address_val_buffer)

	def getProperty(self, name):
		name_buff = array.array('c', name + "\0")
		val_buff = array.array("c", str(0) + "\0")
		address_name_buffer = name_buff.buffer_info()[0]
		address_val_buffer = val_buff.buffer_info()[0]
		self.SendScintilla(QsciScintillaBase.SCI_GETPROPERTY, address_name_buffer, address_val_buffer)
		return ''.join(val_buff)

	def printPropertyAll(self):
		sz = self.SendScintilla(QsciScintillaBase.SCI_PROPERTYNAMES, 0, 0)
		if not sz:
			return
		val_buff = array.array("c", (' ' * sz) + "\0")
		address_val_buffer = val_buff.buffer_info()[0]
		self.SendScintilla(QsciScintillaBase.SCI_PROPERTYNAMES, 0, address_val_buffer)
		print '###>'
		for p in ''.join(val_buff).splitlines():
			v = self.getProperty(p)
			print '    %s = %s' % (p, v)

	def lexer_for_file(self, filename):
		(prefix, ext) = os.path.splitext(filename)
		for (el, lxr) in suffix_to_lexer:
			if ext in el:
				return lxr
		for (el, lxr) in filename_to_lexer:
			if filename in el:
				return lxr
		return QsciLexerCPP

	def set_lexer(self, filename):
		if not self.lexer:
			lexerClass = self.lexer_for_file(filename)
			self.lexer = lexerClass()
			self.setLexer(self.lexer)
			self.setProperty("lexer.cpp.track.preprocessor", "0")
			is_debug = os.getenv("SEASCOPE_QSCI_LEXER_DEBUG", 0)
			if is_debug:
				self.lexer.propertyChanged.connect(self.lpropChanged)
				self.printPropertyAll()


class EditorView(EditorViewBase):
	ev_popup = None
	sig_text_selected = pyqtSignal(str)
	def __init__(self, parent=None):
		EditorViewBase.__init__(self, parent)
		#self.setGeometry(300, 300, 400, 300)

		## Editing line color
		self.setCaretLineVisible(True)
		self.setCaretLineBackgroundColor(QtGui.QColor("#d4feff")) # orig: EEF6FF
		#self.setCaretWidth(2)

		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

		self.codemark_marker = self.markerDefine(self.Circle)

	def get_filename(self):
		return self.filename

	def ed_settings_1(self):
		## Margins colors
		# line numbers margin
		self.setMarginsBackgroundColor(QtGui.QColor("#333333"))
		self.setMarginsForegroundColor(QtGui.QColor("#CCCCCC"))

		# folding margin colors (foreground,background)
		self.setFoldMarginColors(QtGui.QColor("#888888"),QtGui.QColor("#eeeeee"))

		## Edge Mode shows a red vetical bar at 80 chars
		self.setEdgeMode(QsciScintilla.EdgeLine)
		self.setEdgeColumn(80)
		self.setEdgeColor(QtGui.QColor("#FF0000"))

		## Editing line color
		self.setCaretLineVisible(True)
		self.setCaretLineBackgroundColor(QtGui.QColor("#CDA869"))

		## set tab width
		if seascope_editor_tab_width:
			self.setTabWidth(seascope_editor_tab_width)

	def show_line_number_cb(self, val):
		if (val):
			width = self.fm.width( "00000" ) + 5
		else:
			width = 0

		self.setMarginWidth(0, width)
		self.setMarginLineNumbers(0, val)

	def show_folds_cb(self, val):
		if val:
			#self.setMarginsForegroundColor( QtGui.QColor("#404040") )
			#self.setMarginsBackgroundColor( QtGui.QColor("#888888") )

			## Folding visual : we will use circled tree fold
			self.setFolding(QsciScintilla.CircledTreeFoldStyle)
		else:
			self.setFolding(QsciScintilla.NoFoldStyle)
			self.clearFolds()

	def toggle_folds_cb(self):
		self.foldAll()
		
	def codemark_add(self, line):
		self.markerAdd(line, self.codemark_marker)

	def codemark_del(self, line):
		self.markerDelete(line, self.codemark_marker)

	def goto_marker(self, is_next):
		(eline, inx) = self.getCursorPosition()
		if is_next:
			val = self.markerFindNext(eline + 1, -1)
		else:
			val = self.markerFindPrevious(eline - 1, -1)
		if val >= 0:
			self.setCursorPosition(val, 0)

	def open_file_begin(self, filename):
		self.filename = filename

		## Choose a lexer
		self.set_lexer(filename)

		## Braces matching
		self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

		## Render on screen
		self.show()

	def open_file_end(self):
		self.show()
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		#self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setFocus()

	def open_file(self, filename):
		self.open_file_begin(filename)

		## Show this file in the editor
		self.setText(open(filename).read())
		
		## Mark read-only
		self.setReadOnly(True)

		self.open_file_end()

	def refresh_file(self, filename):
		assert filename == self.filename
		pos = self.getCursorPosition()
		self.open_file(filename)
		self.setCursorPosition(*pos)
		self.cursorPositionChanged.emit(*pos)

	def goto_line(self, line):
		line = line - 1
		self.setCursorPosition(line, 0)

		self.ensureLineVisible(line)
		self.setFocus()

	def contextMenuEvent(self, ev):
		if not EditorView.ev_popup:
			return
		f = EditorView.ev_popup.font()
		EditorView.ev_popup.setFont(QFont("San Serif", 8))
		EditorView.ev_popup.exec_(QCursor.pos())
		EditorView.ev_popup.setFont(f)
		
	def mouseReleaseEvent(self, ev):
		super(EditorView, self).mouseReleaseEvent(ev)
		if(self.hasSelectedText()):
			self.query_text = self.selectedText()
			#print 'selectedText ----', self.query_text
			self.sig_text_selected.emit(self.query_text)

class EditorPage(QSplitter):
	def __init__(self, parent=None):
		QSplitter.__init__(self)
		self.fcv = FileContextView(self)
		self.ev = self.new_editor_view()
		self.addWidget(self.fcv)
		self.addWidget(self.ev)
		self.setSizes([1, 300])

		self.ev.cursorPositionChanged.connect(self.fcv.sig_ed_cursor_changed)
		self.fcv.sig_goto_line.connect(self.ev.goto_line)

	def new_editor_view(self):
		return EditorView(self)

	def open_file(self, filename):
		self.ev.open_file(filename)
		self.fcv.run(filename)

	def refresh_file(self):
		filename = self.get_filename()
		self.fcv.rerun(filename)
		self.ev.refresh_file(filename)

	def get_filename(self):
		return self.ev.get_filename()
		
class EditorBook(QTabWidget):
	sig_file_closed = pyqtSignal(str)
	sig_history_update = pyqtSignal(str, int)
	sig_tab_changed = pyqtSignal(str)
	sig_open_dir_view = pyqtSignal(str)
	sig_editor_text_selected = pyqtSignal(str)

	def __init__(self, *args):
		apply(QTabWidget.__init__,(self, ) + args)

		self.setMovable(True)
		self.setTabsClosable(True)
		self.tabCloseRequested.connect(self.removeTab)
		self.currentChanged.connect(self.tab_change_cb)
		
		self.is_show_line = False
		self.is_show_folds = False
		self.f_text = None
		self.ev_font = "Monospace,10,-1,5,50,0,0,0,0,0"

	def new_editor_page(self):
		return EditorPage()

	def addFile(self, fileName):
		ed = self.new_editor_page()
		ed.open_file(fileName)
		ed.ev.set_font(self.ev_font)
		ed.ev.show_line_number_cb(self.is_show_line)
		ed.ev.show_folds_cb(self.is_show_folds)
		self.addTab(ed, os.path.basename(fileName))
		return ed

	def search_already_opened_files(self, filename):
		for i in range(self.count()):
			page = self.widget(i)
			if (page.get_filename() == filename):
				return page
		return None

	def removeTab(self, inx):
		ed = self.widget(inx)
		f = ed.ev.get_filename()
		QTabWidget.removeTab(self, inx)
		self.sig_file_closed.emit(f)

	def clear(self):
		while self.count() != 0:
			self.removeTab(0)

	def remove_tab_list(self, inx_list):
		for inx in sorted(inx_list, reverse=True):
			self.removeTab(inx)

	def tab_list(self, inx, type):
		inx_list = []
		if type == 'all' or type == 'files':
			return range(self.count())
		if type == 'left':
			return range(inx)
		if type == 'right':
			return range(inx + 1, self.count())
		if type == 'other':
			return self.tab_list(inx, 'left') + self.tab_list(inx, 'right')
		assert 0

	def close_list_common(self, type):
		inx_list = self.tab_list(self.currentIndex(), type)
		if len(inx_list) == 0:
			return
		if not DialogManager.show_yes_no('Close all %s ?' % type):
			return
		self.remove_tab_list(inx_list)

	def close_all_left_cb(self):
		self.close_list_common('left')
	def close_all_right_cb(self):
		self.close_list_common('right')
	def close_all_other_cb(self):
		self.close_list_common('other')
	def close_all_cb(self):
		self.close_list_common('files')

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
	def get_file_line_list(self):
		fl_list = []
		tlist = range(self.count())
		inx = self.currentIndex()
		if inx >= 0:
			tlist.append(inx)
		for inx in tlist:
			ed = self.widget(inx)
			(line, inx) = ed.ev.getCursorPosition()
			fl_list.append('%s:%d' % (ed.ev.filename, line + 1))
		return fl_list

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

	def focus_editor(self):
		page = self.currentWidget()
		if page:
			page.ev.setFocus()

	def close_current_page(self):
		self.removeTab(self.currentIndex())
		self.focus_editor()

	def focus_search_ctags(self):
		ed = self.currentWidget()
		if ed:
			ed.fcv.focus_search_ctags()
		
	def copy_edit_cb(self):
		ed = self.currentWidget()
		if ed:
			ed.ev.copy()

	def tab_change_cb(self, inx):
		if (inx == -1):
			fname = ''
		else:
			page = self.currentWidget()
			page.ev.setFocus()
			fname = page.get_filename()
		self.sig_tab_changed.emit(fname)
			
	def open_dir_cb(self):
		page = self.currentWidget()
		if page:
			fname = page.get_filename()
			self.sig_open_dir_view.emit(fname)
			

	def mousePressEvent(self, m_ev):
		QTabWidget.mousePressEvent(self, m_ev)
		if (m_ev.button() == Qt.RightButton):
			# setup popup menu
			self.pmenu = QMenu()
			self.pmenu.addAction("Open dir", self.open_dir_cb)
			self.pmenu.addSeparator()
			self.pmenu.addAction("Close All &Left", self.close_all_left_cb)
			self.pmenu.addAction("Close All &Right", self.close_all_right_cb)
			self.pmenu.addAction("Close &Others", self.close_all_other_cb)
			self.pmenu.addSeparator()
			self.pmenu.addAction("Close &All", self.close_all_cb)
			self.pmenu.exec_(QCursor.pos())

	def show_file_line(self, filename, line, hist=True):
		if line:
			(f, l) = self.get_current_file_line()
			if (f):
				if hist:
					self.sig_history_update.emit(f, l)
		filename = str(filename)
		if (not os.path.exists(filename)):
			return
		page = self.search_already_opened_files(filename)
		if page == None:
			page = self.addFile(filename)
		self.setCurrentWidget(page)
		if line:
			page.ev.goto_line(line)
			if hist:
				self.sig_history_update.emit(filename, line)
		page.ev.setFocus()
		# text selected callback: need to send out again.
		page.ev.sig_text_selected.connect(self.editor_text_selected)

	def editor_text_selected(self, text):
		self.sig_editor_text_selected.emit(text)

	def show_file(self, filename):
		self.show_file_line(filename, 0)

	def show_line(self, line):
		ed = self.currentWidget()
		if not ed:
			return
		ed.ev.goto_line(line)

	def refresh_file_cb(self):
		ed = self.currentWidget()
		if not ed:
			return
		ed.refresh_file()

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

	def change_ev_font(self, font):
		if font == self.ev_font:	
			return
		self.ev_font = font
		for inx in range(self.count()):
			ed = self.widget(inx)
			ed.ev.set_font(self.ev_font)

	def show_line_number_cb(self):
		val = self.m_show_line_num.isChecked()
		self.is_show_line = val
		for inx in range(self.count()):
			ed = self.widget(inx)
			ed.ev.show_line_number_cb(val)

	def show_line_number_pref(self, val):
		if val == self.m_show_line_num.isChecked():
			return
		self.m_show_line_num.setChecked(val)
		self.show_line_number_cb()

	def show_folds_cb(self):
		val = self.m_show_folds.isChecked()
		self.is_show_folds = val
		for inx in range(self.count()):
			ed = self.widget(inx)
			ed.ev.show_folds_cb(val)

	def toggle_folds_cb(self):
		ed = self.currentWidget()
		if not ed:
			return
		if self.is_show_folds:
			ed.ev.toggle_folds_cb()

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

	def codemark_add(self, filename, line):
		ed = self.search_already_opened_files(filename)
		if ed:
			ed.ev.codemark_add(line)

	def codemark_del(self, filename, line):
		ed = self.search_already_opened_files(filename)
		if ed:
			ed.ev.codemark_del(line)

	def bookmark_prev_cb(self):
		ed = self.currentWidget()
		if ed:
			ed.ev.goto_marker(False)

	def bookmark_next_cb(self):
		ed = self.currentWidget()
		if ed:
			ed.ev.goto_marker(True)
