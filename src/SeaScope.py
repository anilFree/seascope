#!/usr/bin/env python

import sys
import os
import string

from PyQt4 import QtGui, QtCore

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import EdView
import ResView
import CallView
import FileView

from CscopeProject import CsQuery

import DialogManager
import ProjectManager
import DebugManager


class SeaScopeApp(QMainWindow):

	def file_preferences_cb(self):
		res = DialogManager.show_preferences_dialog(self.app_style, self.edit_ext_cmd)
		(self.app_style, self.app_font, self.edit_ext_cmd) = res
		if self.edit_ext_cmd != None:
			self.edit_ext_cmd = str(self.edit_ext_cmd).strip()
		if (self.edit_ext_cmd == None or self.edit_ext_cmd == ''):
			self.edit_ext_cmd = 'x-terminal-emulator -e vim %F +%L'
		self.app_write_config()

	def file_close_cb(self):
		self.edit_book.close_current_page()
	def closeEvent(self, ev):
		if (CsQuery.cs_is_open()):
			if not DialogManager.show_yes_no('Close project and quit?'):
				ev.ignore()
				return
		ev.accept()

	def cs_query_cb(self, cmd_id):
		if (not CsQuery.cs_is_open()):
			return
		if (not CsQuery.cs_is_ready()):
			DialogManager.show_msg_dialog('\nProject has no source files')
			return
		req = self.edit_book.get_current_word()
		if (req != None):
			req = str(req).strip()
		opt = None
		if (cmd_id < 10 or cmd_id == 12):
			val = DialogManager.show_query_dialog(cmd_id, req)
			if (val == None):
				return
			(cmd_id, req, opt) = val
		if (req == None or req == ''):
			return
		#self.sbar.showMessage('Query: ' + str(cmd_id) + ': ' + req)
		if (cmd_id < 9):
			self.do_cs_query(cmd_id, req, opt)
		else:
			if cmd_id == 11:
				self.do_cs_query_qdef(1, req, opt)
			elif cmd_id == 9:
				self.do_cs_query_ctree(3, req, opt)
		#self.sbar.clearMessage()
				

	def cb_ref(self):
		self.cs_query_cb(0)
	def cb_def(self):
		self.cs_query_cb(1)
	def cb_called(self):
		self.cs_query_cb(2)
	def cb_calling(self):
		self.cs_query_cb(3)
	def cb_text(self):
		self.cs_query_cb(4)
	def cb_egrep(self):
		self.cs_query_cb(5)
	def cb_file(self):
		self.cs_query_cb(7)
	def cb_inc(self):
		self.cs_query_cb(8)
	def cb_call_tree(self):
		self.cs_query_cb(9)
	def cb_quick_def(self):
		self.cs_query_cb(11)
	def cb_rebuild(self):
		sig_rebuild = CsQuery.cs_rebuild()
		dlg = QProgressDialog()
		dlg.setWindowTitle('SeaScope rebuild')
		dlg.setLabelText('Rebuilding cscope database...')
		dlg.setCancelButton(None)
		dlg.setMinimum(0)
		dlg.setMaximum(0)
		sig_rebuild.connect(dlg.accept)
		while dlg.exec_() != QDialog.Accepted:
			pass

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
		self.file_view.le.setFocus()
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
		m_prj.addAction('&Settings', self.proj_settings_cb)
		m_prj.addSeparator()
		m_prj.addAction('&Close Project', self.proj_close_cb)

		m_cscope = menubar.addMenu('&Cscope')
		m_cscope.setFont(QFont("San Serif", 8))
		self.m_cscope = m_cscope
		EdView.EditorView.ev_popup = m_cscope
		m_cscope.addAction('&References', self.cb_ref, 'Ctrl+0')
		m_cscope.addAction('&Definitions', self.cb_def, 'Ctrl+1')
		m_cscope.addAction('&Called Functions', self.cb_called, 'Ctrl+2')
		m_cscope.addAction('C&alling Functions', self.cb_calling, 'Ctrl+3')
		m_cscope.addAction('Find &Text', self.cb_text, 'Ctrl+4')
		m_cscope.addAction('Find &Egrep', self.cb_egrep, 'Ctrl+5')
		m_cscope.addAction('Find &File', self.cb_file, 'Ctrl+7')
		m_cscope.addAction('&Including Files', self.cb_inc, 'Ctrl+8')
		m_cscope.addSeparator()
		m_cscope.addAction('&Quick Definition', self.cb_quick_def, 'Ctrl+]')
		m_cscope.addAction('Call Tr&ee', self.cb_call_tree, 'Ctrl+\\')
		m_cscope.addSeparator()
		m_cscope.addAction('Re&build Database', self.cb_rebuild)

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
		m_help.addAction('About SeaScope', self.help_about_cb)
		m_help.addAction('About Qt', QApplication.aboutQt)

	# app config
	def app_get_config_file(self):
		config_file = '~/.seascoperc'
		return os.path.expanduser(config_file)

	def app_read_config(self):
		self.recent_projects = []
		self.app_style = None
		self.app_font = None
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
			if (key == 'edit_ext_cmd'):
				self.edit_ext_cmd = line[1]
		cf.close()

	def app_write_config(self):
		cf = open(self.app_get_config_file(), 'w')
		cf.write('recent_projects' + '=' + string.join(self.recent_projects, ',')+ '\n')
		if (self.app_style):
			cf.write('app_style' + '=' + self.app_style + '\n')
		if (self.app_font):
			cf.write('app_font' + '=' + self.app_font + '\n')
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

	def do_cs_query(self, cmd_id, req, opt):
		book = self.res_book
		## create page
		page = ResView.ResultManager.create_result_page(book, cmd_id, req)
		## add result
		sig_res = CsQuery.cs_query(cmd_id, req, opt)
		sig_res[0].connect(page.add_result)
		#page.add_result(req, res)
		DebugManager.connect_to_cs_sig_res(sig_res[1])

	def cs_qdef_result(self, req, res):
		count = len(res)
		if count > 1:
			page = ResView.ResultPage()
			page.add_result(req, res)
			
			dlg = QDialog()
			dlg.setWindowTitle('Quick Definition: ' + req)
			vlay = QVBoxLayout(dlg)
			vlay.addWidget(page)

			page.sig_show_file_line.connect(self.edit_book.show_file_line)
			page.activated.connect(dlg.accept)
			page.setMinimumWidth(800)
			page.setMinimumHeight(100)

			dlg.exec_()
			return
		if (count == 1):
			filename = res[0][1]
			try:
				line = int(res[0][2])
			except:
				return
			self.edit_book.show_file_line(filename, line)

	def do_cs_query_qdef(self, cmd_id, req, opt):
		sig_res = CsQuery.cs_query(cmd_id, req, opt)
		sig_res[0].connect(self.cs_qdef_result)
		DebugManager.connect_to_cs_sig_res(sig_res[1])

	def ctree_show_file_line(self, filename, line):
		self.raise_()
		self.activateWindow()
		self.edit_book.show_file_line(filename, line)

	def do_cs_query_ctree(self, cmd_id, req, opt):
		w = CallView.CallTreeWindow(self, req)
		w.sig_show_file_line.connect(self.ctree_show_file_line)
		w.show()
		
	# project menu functions
	def proj_new_or_open(self):
		self.editor_tab_changed_cb('SeaScope')
		self.update_recent_projects(CsQuery.cs_get_proj_dir())
		self.file_view.add_files(CsQuery.cs_get_proj_src_files())

	def proj_new_cb(self):
		if (CsQuery.cs_is_open()):
			if (not DialogManager.show_proj_close()):
				return
			self.proj_close_cb()
		proj_args = ProjectManager.show_project_dialog(None)
		if (proj_args != None):
			CsQuery.cs_proj_new(proj_args)
			self.proj_new_or_open()

	def proj_open(self, proj_path):
		CsQuery.cs_proj_open(proj_path)
		self.proj_new_or_open()
	def proj_open_cb(self):
		proj_path = DialogManager.show_project_open_dialog(self.recent_projects)
		if (proj_path != None):
			self.proj_close_cb()
			self.proj_open(proj_path)

	def proj_close_cb(self):
		if (not CsQuery.cs_is_open()):
			return
		
		self.update_recent_projects(CsQuery.cs_get_proj_dir())
		self.setWindowTitle("SeaScope")

		CsQuery.cs_proj_close()
		
		self.edit_book.clear()
		self.res_book.clear()
		self.file_view.clear()

	def proj_settings_cb(self):
		if (not CsQuery.cs_is_open()):
			return
		proj_args = CsQuery.cs_get_proj_conf()
		proj_args = ProjectManager.show_project_dialog(proj_args)
		if (proj_args == None):
			return
		CsQuery.cs_proj_update(proj_args)
		self.file_view.add_files(CsQuery.cs_get_proj_src_files())

	def editor_tab_changed_cb(self, fname):
		title = CsQuery.cs_get_proj_name()
		if not title:
			title = 'SeaScope'
		if (fname and fname != ''):
			title = title + ' - ' + fname
		self.setWindowTitle(title)

	def __init__(self, parent=None):
		QMainWindow.__init__(self)
		
		self.edit_book = EdView.EditorBook()
		self.res_book = ResView.ResultManager()
		self.file_view = FileView.FileTree()

		self.sbar = self.statusBar()
		self.create_mbar()


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
		self.setWindowTitle('SeaScope')
		self.setGeometry(300, 100, 800, 600)
		#self.showMaximized()

		QApplication.setWindowIcon(QIcon('icons/seascope.svg'))

		self.app_read_config()
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
	os.chdir(os.path.dirname(os.path.realpath(__file__)))

	app = QApplication(sys.argv)
	ma = SeaScopeApp()
	ma.show()
	sys.exit(app.exec_())
