#!/usr/bin/env python

import sys
import os
import string

try:
	from PyQt4 import QtGui, QtCore
except ImportError:
	print 'Error: PyQt4 package not found\nError: required packages: PyQt4 (>4.5) and qscintilla-python\nError: program aborted.'
	sys.exit(-1)

try:
	from PyQt4.QtGui import *
	from PyQt4.QtCore import *
	from view import EdView, ResView, FileView, CallView
	import backend
	from backend.plugins import PluginHelper
	import DialogManager
	import DebugManager
except ImportError:
	print "Error: failed to import supporting packages.\nError: program aborted."
	sys.exit(-1)

class SeascopeApp(QMainWindow):

	def file_preferences_cb(self):
		ev_font = QFont()
		ev_font.fromString(self.edit_book.ev_font)
		res = DialogManager.show_preferences_dialog(self.app_style, self.edit_ext_cmd, ev_font, self.exit_dont_ask)
		(self.app_style, self.app_font, self.edit_ext_cmd, ev_font, self.exit_dont_ask) = res
		if self.edit_ext_cmd != None:
			self.edit_ext_cmd = str(self.edit_ext_cmd).strip()
		if (self.edit_ext_cmd == None or self.edit_ext_cmd == ''):
			self.edit_ext_cmd = 'x-terminal-emulator -e vim %F +%L'
		self.edit_book.change_ev_font(ev_font.toString())
		self.app_write_config()

	def file_close_cb(self):
		self.edit_book.close_current_page()
	def closeEvent(self, ev):
		if not self.exit_dont_ask and backend.proj_is_open():
			ret = DialogManager.show_yes_no_dontask('Close project and quit?')
			if ret == 1:
				ev.ignore()
				return
			if ret == 2:
				self.exit_dont_ask = True
		self.app_write_config()
		ev.accept()

	def go_prev_res_cb(self):
		self.res_book.go_next_res(-1)
	def go_next_res_cb(self):
		self.res_book.go_next_res(+1)
	def go_prev_pos_cb(self):
		self.res_book.go_next_history(-1)
	def go_next_pos_cb(self):
		self.res_book.go_next_history(+1)
	def go_pos_history_cb(self):
		self.res_book.show_history()
	def go_search_file_list_cb(self):
		self.file_view.search_file_cb()
	def go_search_ctags_cb(self):
		self.edit_book.focus_search_ctags()


	def help_about_cb(self):
		DialogManager.show_about_dialog()

	def external_editor_cb(self):
		self.edit_book.open_in_external_editor(self.edit_ext_cmd)

	def show_dbg_dialog(self):
		DebugManager.show_dbg_dialog(self)

	def create_mbar(self):
		menubar = self.menuBar()

		m_file = menubar.addMenu('&File')
		m_file.addAction('&Preferences', self.file_preferences_cb)
		m_file.addAction('&Debug', self.show_dbg_dialog, 'Ctrl+D')
		m_file.addSeparator()
		m_file.addAction('&Close', self.file_close_cb, QKeySequence.Close)
		m_file.addAction('&Quit', self.close, QKeySequence.Quit)

		m_edit = menubar.addMenu('&Edit')
		m_edit.addAction('&Find...', self.edit_book.find_cb, 'Ctrl+F')
		m_edit.addAction('Find &Next', self.edit_book.find_next_cb, 'F3')
		m_edit.addAction('Find &Previous', self.edit_book.find_prev_cb, 'Shift+F3')
		m_edit.addSeparator()
		self.edit_book.m_show_line_num = m_edit.addAction('Show line number', self.edit_book.show_line_number_cb, 'F11')
		self.edit_book.m_show_line_num.setCheckable(True)

		m_edit.addSeparator()
		m_edit.addAction('Matching brace', self.edit_book.matching_brace_cb, 'Ctrl+6')
		m_edit.addAction('Goto line', self.edit_book.goto_line_cb, 'Ctrl+G')
		m_edit.addAction('External editor', self.external_editor_cb, 'Ctrl+E');

		m_prj = menubar.addMenu('&Project')
		m_prj.addAction('&New Project', self.proj_new_cb)
		m_prj.addAction('&Open Project', self.proj_open_cb)
		m_prj.addSeparator()
		
		act = m_prj.addAction('&Settings', self.proj_settings_cb)
		act.setDisabled(True)
		backend.prj_actions.append(act)
		act = m_prj.addAction('&Close Project', self.proj_close_cb)
		act.setDisabled(True)
		backend.prj_actions.append(act)

		self.backend_menu = menubar.addMenu('')

		m_go = menubar.addMenu('&Go')
		m_go.addAction('Previous Result', self.go_prev_res_cb, 'Alt+Up')
		m_go.addAction('Next Result', self.go_next_res_cb, 'Alt+Down')
		m_go.addSeparator()
		m_go.addAction('Previous Position', self.go_prev_pos_cb, 'Alt+Left')
		m_go.addAction('Next Position', self.go_next_pos_cb, 'Alt+Right')
		m_go.addAction('Position History', self.go_pos_history_cb, 'Ctrl+H')
		m_go.addSeparator()
		m_go.addAction('Search file list', self.go_search_file_list_cb, 'Ctrl+Shift+O')
		m_go.addAction('Search ctags', self.go_search_ctags_cb, 'Ctrl+Shift+T')
		
		m_help = menubar.addMenu('&Help')
		m_help.addAction('About Seascope', self.help_about_cb)
		m_help.addAction('About Qt', QApplication.aboutQt)

	# app config
	def app_get_config_file(self):
		config_file = '~/.seascoperc'
		return os.path.expanduser(config_file)

	def app_read_config(self):
		self.recent_projects = []
		self.app_style = None
		self.app_font = None
		self.exit_dont_ask = False
		self.edit_ext_cmd = 'x-terminal-emulator -e vim %F +%L'

		path = self.app_get_config_file()
		if (not os.path.exists(path)):
			return
		cf = open(path, 'r')
		for line in cf:
			line = line.split('=', 1)
			key = line[0].strip()
			if (key == 'recent_projects'):
				for path in line[1].split(','):
					path=path.strip()
					if (os.path.isdir(path)):
						self.recent_projects.append(path)
			if (key == 'app_style'):
				self.app_style = line[1].split('\n')[0]
			if (key == 'app_font'):
				self.app_font = line[1].split('\n')[0]
			if (key == 'edit_font'):
				self.edit_book.ev_font = line[1].split('\n')[0]
			if (key == 'edit_show_line_num'):
				if ('true' == line[1].split('\n')[0]):
					self.edit_book.is_show_line = True
			if (key == 'edit_ext_cmd'):
				self.edit_ext_cmd = line[1]
			if (key == 'exit_dont_ask'):
				if ('true' == line[1].split('\n')[0]):
					self.exit_dont_ask = True
		cf.close()

	def app_write_config(self):
		cf = open(self.app_get_config_file(), 'w')
		cf.write('recent_projects' + '=' + string.join(self.recent_projects, ',')+ '\n')
		if (self.app_style):
			cf.write('app_style' + '=' + self.app_style + '\n')
		if (self.app_font):
			cf.write('app_font' + '=' + self.app_font + '\n')
		if (self.edit_book.ev_font):
			cf.write('edit_font' + '=' + self.edit_book.ev_font + '\n')
		if (self.edit_book.is_show_line):
			cf.write('edit_show_line_num' + '=' + 'true' + '\n')
		if (self.exit_dont_ask):
			cf.write('exit_dont_ask' + '=' + 'true' + '\n')
		if (self.edit_ext_cmd):
			cf.write('edit_ext_cmd' + '=' + self.edit_ext_cmd + '\n')
		cf.close()
		
	def update_recent_projects(self, path):
		if (path == None or path == ""):
			return
		new_list = [path]
		for ele in self.recent_projects:
			if ele != path:
				new_list.append(ele)
		self.recent_projects = new_list
		self.app_write_config()


	# project menu functions
	def proj_new_or_open(self):
		self.editor_tab_changed_cb('Seascope')
		self.update_recent_projects(backend.proj_dir())

	def proj_new_cb(self):
		if (backend.proj_is_open()):
			if (not DialogManager.show_proj_close()):
				return
			self.proj_close_cb()
		if backend.proj_new():
			self.proj_new_or_open()

	def proj_open(self, proj_path):
		rc = backend.proj_open(proj_path)
		if not rc:
			print 'proj_open', proj_path, 'failed'
			return
		self.proj_new_or_open()
	def proj_open_cb(self):
		proj_path = DialogManager.show_project_open_dialog(self.recent_projects)
		if (proj_path != None):
			if backend.proj_is_open():
				self.proj_close_cb()
			self.proj_open(proj_path)

	def proj_close_cb(self):
		self.update_recent_projects(backend.proj_dir())
		self.setWindowTitle("Seascope")

		backend.proj_close()
		
		self.edit_book.clear()
		self.res_book.clear()
		self.file_view.clear()

	def proj_settings_cb(self):
		backend.proj_settings_trigger()

	def editor_tab_changed_cb(self, fname):
		title = backend.proj_name()
		if not title:
			title = 'Seascope'
		if (fname and fname != ''):
			title = title + ' - ' + fname
		self.setWindowTitle(title)

	def show_file_line(self, filename, line):
		self.edit_book.show_file_line(filename, line)

	def __init__(self, parent=None):
		QMainWindow.__init__(self)

		self.edit_book = EdView.EditorBook()
		self.res_book = ResView.ResultManager()
		self.file_view = FileView.FileTree()

		self.sbar = self.statusBar()
		self.create_mbar()

		EdView.EditorView.ev_popup = self.backend_menu
		CallView.CallTreeWindow.parent = self

		PluginHelper.backend_menu = self.backend_menu
		PluginHelper.edit_book = self.edit_book
		PluginHelper.res_book = self.res_book
		PluginHelper.call_view = CallView
		PluginHelper.file_view = self.file_view
		PluginHelper.dbg_mgr = DebugManager
		

		self.edit_book.sig_history_update.connect(self.res_book.history_update)
		self.edit_book.sig_tab_changed.connect(self.editor_tab_changed_cb)
		self.res_book.sig_show_file_line.connect(self.edit_book.show_file_line)
		self.file_view.sig_show_file.connect(self.edit_book.show_file)

		self.hsp = QSplitter();
		self.hsp.addWidget(self.edit_book)
		self.hsp.addWidget(self.file_view)
		self.hsp.setSizes([700, 1])

		self.vsp = QSplitter();
		self.vsp.setOrientation(Qt.Vertical)
		self.vsp.addWidget(self.hsp)
		self.vsp.addWidget(self.res_book)
		self.vsp.setSizes([1, 1])

		self.setCentralWidget(self.vsp)
		self.setWindowTitle('Seascope')
		self.setGeometry(300, 100, 800, 600)
		#self.showMaximized()

		QApplication.setWindowIcon(QIcon('icons/seascope.svg'))

		self.app_read_config()
		self.edit_book.m_show_line_num.setChecked(self.edit_book.is_show_line)
		if len(self.recent_projects):
			self.proj_open(self.recent_projects[0])
		else:
			self.proj_open_cb()
		if (self.app_style):
			QApplication.setStyle(self.app_style)
		if (self.app_font):
			font = QFont()
			font.fromString(self.app_font)
			QApplication.setFont(font)

if __name__ == "__main__":

	# pyqt version 4.5 is required
	pyqt_required_version = 0x40500 
	if not QtCore.PYQT_VERSION >= pyqt_required_version:
		print 'Needs pyqt version > 4.5'
		sys.exit(-1)

	# change working dir to the script dir so that we can run this script anywhere else
	app_dir = os.path.dirname(os.path.realpath(__file__))
	os.chdir(app_dir)
	
	backend.load_plugins()

	app = QApplication(sys.argv)
	ma = SeascopeApp()
	ma.show()
	sys.exit(app.exec_())
