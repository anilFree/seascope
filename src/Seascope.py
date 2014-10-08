#!/usr/bin/env python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import sys
sys.dont_write_bytecode = True

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
	from PyQt4 import uic
	from view import EdView, EdViewRW, ResView, FileView, CallView, ClassGraphView, FileFuncGraphView
	from view import DebugView, CodemarkView, CodeContextView
	from view import ProjectUi
	import backend
	import DialogManager
	import view
except ImportError:
	print "Error: failed to import supporting packages.\nError: program aborted."
	sys.exit(-1)

def msg_box(msg):
	QMessageBox.warning(None, "Seascope", msg, QMessageBox.Ok)

class BackendChooserDialog(QDialog):
	def __init__(self):
		QDialog.__init__(self)
		self.ui = uic.loadUi('ui/proj_new.ui', self)
		self.backend_lw.currentRowChanged.connect(self.currentRowChanged_cb)

		self.backend = backend

	def currentRowChanged_cb(self, row):
		if row == -1:
			return
		bname = str(self.backend_lw.currentItem().text())
		desc = ''
		for b in self.backend.plugin_list():
			if b.name() == bname:
				desc = b.description()
		self.descr_te.setText(desc)

	def run_dialog(self):
		blist = self.backend.plugin_list()
		if len(blist) == 0:
			msg_box('No backends are available/usable')
			return None
		bi = [ b.name() for b in blist ]
		self.backend_lw.addItems(bi)
		self.backend_lw.setCurrentRow(0)
		if self.exec_() == QDialog.Accepted:
			bname = str(self.backend_lw.currentItem().text())
			return bname
		return None

class QueryUiHelper:
	def __init__(self):
		self.edit_book = None
		self.res_book = None
		self.call_view = None
		self.class_graph_view = None
		self.file_func_graph_view = None
		self.dbg_view = None
		self.file_view = None

	def editor_current_file(self):
		(f, l) = self.edit_book.get_current_file_line()
		return f

	def editor_current_word(self):
		return self.edit_book.get_current_word()

	def result_page_new(self, name, sig_res):
		if sig_res == None:
			return
		page = self.res_book.create_result_page(name)
		## add result
		sig_res[0].connect(page.add_result)
		#page.add_result(req, res)
		self.dbg_view.connect_to_sig(sig_res[1])

	def file_view_update(self, flist):
		self.file_view.add_files(flist)

	def _quick_def_result(self, req, res):
		count = len(res)
		if count > 1:
			page = self.res_book.create_result_page_single()
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

	def quick_def_page_new(self, sig_res):
		if sig_res == None:
			return
		sig_res[0].connect(self._quick_def_result)
		self.dbg_view.connect_to_sig(sig_res[1])

	def call_view_page_new(self, req, query_func, ctree_query_args, opt):
		hint_file = self.editor_current_file()
		self.call_view.create_page(req, query_func, ctree_query_args, opt, hint_file)

	def class_graph_view_page_new(self, req, dname, prj_type, query_func, clgraph_query_args, opt):
		self.class_graph_view.create_page(req, dname, prj_type, query_func, clgraph_query_args, opt)

	def file_func_graph_view_page_new(self, req, dname, proj_dir, query_func, ffgraph_query_args, opt):
		self.file_func_graph_view.create_page(req, dname, proj_dir, query_func, ffgraph_query_args, opt)


class QueryDialogUi(QDialog):
	def __init__(self, title, feat):
		QDialog.__init__(self)

		self.feat = feat
		self.ui = uic.loadUi('ui/query.ui', self)
		self.qd_sym_inp.setAutoCompletion(False)
		self.qd_sym_inp.setInsertPolicy(QComboBox.InsertAtTop)

		self.setWindowTitle(title)
		self.qd_cmd_inp.addItems(self.feat.cmd_qstrlist)

	def run_dialog(self, cmd_str, req):
		qstr = self.feat.cmd_str2qstr[cmd_str]
		inx = self.qd_cmd_inp.findText(qstr)
		self.qd_cmd_inp.setCurrentIndex(inx)
		if req == None:
			req = ''
		self.qd_sym_inp.setFocus()
		self.qd_sym_inp.setEditText(req)
		self.qd_sym_inp.lineEdit().selectAll()
		self.qd_substr_chkbox.setChecked(False)
		self.qd_icase_chkbox.setChecked(False)

		self.show()
		if self.exec_() == QDialog.Accepted:
			req = str(self.qd_sym_inp.currentText())
			cmd = str(self.qd_cmd_inp.currentText())
			cmd_str = self.feat.cmd_qstr2str[cmd]
			#self.qd_sym_inp.addItem(req)
			in_opt = {
				'substring'   : self.qd_substr_chkbox.isChecked(),
				'ignorecase'  : self.qd_icase_chkbox.isChecked(),
			}
			res = self.feat.query_dlg_cb(req, cmd_str, in_opt)
			return res
		return None

	def show_dlg(self, cmd_str, req):
		return self.run_dialog(cmd_str, req)

class QueryUi(QObject):
	def __init__(self, h):
		QObject.__init__(self)
		self.qui_h = h
		self.backend = backend
		self.backend_menu = None
		self.prj_actions = []

		self.feat = None
		self.qry_ui = None

	def set_backend_menu(self, menu):
		self.backend_menu = menu
		self.backend_menu.triggered.connect(self.menu_cb)

	def setup(self):
		self.prepare_menu()
		for act in self.prj_actions:
			act.setEnabled(True)

		self.feat = self.backend.proj_feature()
		t = backend.proj_type().title() + ' Query'
		self.qry_ui = QueryDialogUi(t, self.feat)

		self.query_file_list()

	def reset(self):
		self.backend_menu.clear()
		self.backend_menu.setTitle('')
		for act in self.prj_actions:
			act.setEnabled(False)
		
		self.feat = None
		self.qry_ui = None

	def editor_current_file(self):
		return self.qui_h.editor_current_file()

	def editor_current_word(self):
		return self.qui_h.editor_current_word()

	def prepare_menu(self):
		td = {
			'idutils' : '&Idutils',
			'gtags'   : 'G&tags',
			'cscope'  : '&Cscope',
		}
		t = td[self.backend.proj_type()]
		menu = self.backend_menu
		menu.setTitle(t)
		feat = self.backend.proj_feature()
		for c in feat.menu_cmd_list:
			if c[0] == '---':
				menu.addSeparator()
				continue
			if c[2] == None:
				if c[0] == 'UPD':
					func = self.rebuild_cb
					act = menu.addAction(c[1], func)
				act.cmd_str = None
			else:
				act = menu.addAction(c[1])
				act.setShortcut(c[2])
				act.cmd_str = c[0]

	def menu_cb(self, act):
		if act.cmd_str != None:
			self.query_cb(act.cmd_str)

	def query_cb(self, cmd_str):
		if not backend.proj_conf():
			return
		if not backend.proj_is_ready():
			show_msg_dialog('\nProject has no source files')
			return

		if cmd_str == 'CLGRAPHD':
			f = self.editor_current_file()
			if f:
				d = os.path.dirname(f)
				self.query_class_graph_dir(d)
			return
		if cmd_str == 'FFGRAPH':
			f = self.editor_current_file()
			if f:
				self.query_file_func_graph(f)
			return

		req = self.editor_current_word()
		if (req != None):
			req = str(req).strip()
		opt = None
		if cmd_str not in [ 'QDEF' ]:
			val = self.qry_ui.show_dlg(cmd_str, req)
			if val == None:
				return
			(cmd_str, req, opt) = val
		if (req == None or req == ''):
			return

		if cmd_str == 'QDEF':
			self.query_qdef(req, opt)
		elif cmd_str == 'CTREE':
			self.query_ctree(req, opt)
		elif cmd_str == 'CLGRAPH':
			self.query_class_graph(req, opt)
		else:
			self.do_query(cmd_str, req, opt)

	def do_proj_query(self, rquery):
		print 'do_proj_query', rquery
		sig_res = self.backend.proj_query(rquery)
		return sig_res

	def query_ctree(self, req, opt):
		self.qui_h.call_view_page_new(req, self.do_proj_query, self.feat.ctree_query_args, opt)

	def query_class_graph(self, req, opt):
		prj_type = self.backend.proj_type()
		prj_dir = self.backend.proj_dir()
		self.qui_h.class_graph_view_page_new(req, prj_dir, prj_type, self.do_proj_query, self.feat.clgraph_query_args, opt)

	def query_class_graph_dir(self, dname):
		opt = []
		self.qui_h.class_graph_view_page_new('', dname, None, self.do_proj_query, self.feat.clgraph_query_args, opt)

	def query_file_func_graph(self, fname):
		opt = []
		self.qui_h.file_func_graph_view_page_new('', fname, '', self.do_proj_query, self.feat.ffgraph_query_args, opt)

	def _prepare_rquery(self, cmd_str, req, opt):
		rquery = {}
		rquery['cmd'] = cmd_str
		rquery['req'] = req
		rquery['opt'] = opt
		# add current file info
		rquery['hint_file'] = self.editor_current_file()
		return rquery

	def query_qdef(self, req, opt):
		rquery = {}
		rquery = self._prepare_rquery('DEF', req, opt)
		sig_res = self.do_proj_query(rquery)
		self.qui_h.quick_def_page_new(sig_res)

	def do_query(self, cmd_str, req, opt):
		## create page
		name = cmd_str + ' ' + req
		rquery = self._prepare_rquery(cmd_str, req, opt)
		sig_res = self.do_proj_query(rquery)
		self.qui_h.result_page_new(name, sig_res)

	def do_rebuild(self):
		sig_rebuild = self.backend.proj_rebuild()
		if not sig_rebuild:
			return
		dlg = QProgressDialog()
		dlg.setWindowTitle('Seascope rebuild')
		dlg.setLabelText('Rebuilding database...')
		dlg.setCancelButton(None)
		dlg.setMinimum(0)
		dlg.setMaximum(0)
		sig_rebuild.connect(dlg.accept)
		while dlg.exec_() != QDialog.Accepted:
			pass
		self.query_file_list()


	def rebuild_cb(self):
		self.do_rebuild()

	def query_file_list(self):
		sig_res = self.backend.proj_query_fl()
		if sig_res == None:
			return
		if isinstance(sig_res , list):
			fl = sig_res
			self.qui_h.file_view_update(fl)
			return
		sig_res.connect(self.qui_h.file_view_update)

class SeascopeApp(QMainWindow):

	def file_preferences_cb(self):
		ev_font = QFont()
		ev_font.fromString(self.edit_book.ev_font)
		res = DialogManager.show_preferences_dialog(self.app_style, self.edit_ext_cmd, ev_font, self.exit_dont_ask, self.inner_editing, self.eb_is_show_line)
		(self.app_style, self.app_font, self.edit_ext_cmd, ev_font, self.exit_dont_ask, self.inner_editing_conf, self.eb_is_show_line) = res
		if self.edit_ext_cmd != None:
			self.edit_ext_cmd = str(self.edit_ext_cmd).strip()
		if (self.edit_ext_cmd == None or self.edit_ext_cmd == ''):
			self.edit_ext_cmd = 'x-terminal-emulator -e vim %F +%L'
		self.edit_book.change_ev_font(ev_font.toString())
		self.code_ctx_view.change_ev_font(ev_font.toString())
		self.edit_book.show_line_number_pref(self.eb_is_show_line)
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

		# extra proc for editing enabled
		if self.inner_editing:
			self.edit_book.close_all_cb()

		self.app_write_config()
		if backend.proj_is_open():
			self.app_gui_state_save(backend.proj_dir())
		ev.accept()
	def file_restart_cb(self):
		if not DialogManager.show_yes_no('Restart ?'):
			return
		hint = self.edit_book.get_file_line_list()
		if backend.proj_is_open():
			self.proj_close_cb()
		QApplication.quit()
		os.environ['SEASCOPE_RESTART_HINT'] = '%s' % str(hint)
		QProcess.startDetached(sys.executable, QApplication.arguments(), self.seascope_start_dir);
	def file_restarted_cb(self):
		try:
			hint = os.environ['SEASCOPE_RESTART_HINT']
			#del os.environ['SEASCOPE_RESTART_HINT']
			fll = eval(hint)
			for fl in fll:
				try:
					(f, l) = fl.rsplit(':', 1)
					l = int(l)
					self.edit_book.show_file_line(f, l, hist=False)
				except Exception as e:
					print e
		except:
			pass

	def codemark_add(self, f, l):
		self.cm_mgr.append(f, l)
		self.edit_book.codemark_add(f, l - 1)
		actionText = QString(f + " : " + str(l))
		act = QAction(actionText, self)
		self.cm_actionGroup.addAction(act)
		self.m_cm.addAction(act)

	def codemark_delete(self, f, l):
		self.cm_mgr.delete(f, l)
		self.edit_book.codemark_del(f, l - 1)
		actionText = QString(f + " : " + str(l))
		actions = self.cm_actionGroup.actions()
		for act in actions:
			if actionText == act.text():
				self.cm_actionGroup.removeAction(act)
		
	def codemark_toggle_cb(self):
		(f, l) = self.edit_book.get_current_file_line()
		if self.cm_mgr.check(f, l) == 0:
			self.codemark_add(f, l)
		else:
			self.codemark_delete(f, l)

	def codemark_del_file_cb(self, filename):
		if filename == '':
			return
		for f, l in reversed(self.cm_mgr.codemarks()):
			if f == filename:
				self.codemark_delete(f, l)

	def codemark_del_all_cb(self):
		if not self.cm_mgr.count():
			return
		if not DialogManager.show_yes_no('Delete all codemarks ?'):
			return
		for f, l in reversed(self.cm_mgr.codemarks()):
			self.codemark_delete(f, l)
		
	def codemark_go(self, action):
		for f, l in self.cm_mgr.codemarks():
			if action.text() == QString(f + " : " + str(l)):
				self.edit_book.show_file_line(f, l)
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
		DebugView.show_dbg_dialog(self)

	def create_mbar(self):
		menubar = self.menuBar()

		m_file = menubar.addMenu('&File')
		m_file.addAction('&Preferences', self.file_preferences_cb)
		m_file.addAction('&Debug', self.show_dbg_dialog, 'Ctrl+D')
		m_file.addSeparator()
		if self.inner_editing:
			m_file.addAction('&Save', self.edit_book.save_current_page, 'Ctrl+S')
		m_file.addAction('&Close', self.file_close_cb, QKeySequence.Close)
		m_file.addSeparator()
		m_file.addAction('&Restart', self.file_restart_cb, QKeySequence.Quit)
		m_file.addAction('&Quit', self.close, QKeySequence.Quit)

		m_edit = menubar.addMenu('&Edit')
		
		if self.inner_editing:
			m_edit.addAction('Undo', self.edit_book.undo_edit_cb, 'Ctrl+Z')
			m_edit.addAction('Rebo', self.edit_book.redo_edit_cb, 'Ctrl+Y')
			m_edit.addSeparator()
		m_edit.addAction('Copy', self.edit_book.copy_edit_cb, 'Ctrl+C')
		if self.inner_editing:
			m_edit.addAction('Paste', self.edit_book.paste_edit_cb, 'Ctrl+V')
			m_edit.addAction('Cut', self.edit_book.cut_edit_cb, 'Ctrl+X')
		m_edit.addSeparator()	

		m_edit.addAction('&Find...', self.edit_book.find_cb, 'Ctrl+F')
		m_edit.addAction('Find &Next', self.edit_book.find_next_cb, 'F3')
		m_edit.addAction('Find &Previous', self.edit_book.find_prev_cb, 'Shift+F3')

		m_edit.addSeparator()
		self.edit_book.m_show_line_num = m_edit.addAction('Show line number', self.edit_book.show_line_number_cb, 'F11')
		self.edit_book.m_show_line_num.setCheckable(True)
		self.edit_book.m_show_line_num.setChecked(True)
		self.show_toolbar = m_edit.addAction('Show toolbar', self.show_toolbar_cb, 'F4')
		self.show_toolbar.setCheckable(True)

		m_edit.addSeparator()
		self.edit_book.m_show_folds = m_edit.addAction('Show folds', self.edit_book.show_folds_cb)
		self.edit_book.m_show_folds.setCheckable(True)
		self.toggle_folds = m_edit.addAction('Toggle folds', self.edit_book.toggle_folds_cb)
		
		m_edit.addSeparator()
                m_edit.addAction('Refresh file', self.edit_book.refresh_file_cb, 'F5')
		m_edit.addAction('Matching brace', self.edit_book.matching_brace_cb, 'Ctrl+6')
		m_edit.addAction('Goto line', self.edit_book.goto_line_cb, 'Ctrl+G')
		m_edit.addAction('External editor', self.external_editor_cb, 'Ctrl+E');

		m_prj = menubar.addMenu('&Project')
		m_prj.addAction('&New Project', self.proj_new_cb)
		m_prj.addAction('&Open Project', self.proj_open_cb)
		m_prj.addSeparator()
		
		act = m_prj.addAction('&Settings', self.proj_settings_cb)
		act.setDisabled(True)
		self.qui.prj_actions.append(act)
		act = m_prj.addAction('&Close Project', self.proj_close_cb)
		act.setDisabled(True)
		self.qui.prj_actions.append(act)

		self.backend_menu = menubar.addMenu('')

		self.m_cm = menubar.addMenu('&Codemark')
		self.m_cm.addAction('Toggle codemark', self.codemark_toggle_cb, 'Ctrl+B')
		self.m_cm.addAction('Delete all codemarks', self.codemark_del_all_cb, '')
		self.m_cm.addSeparator()
		self.m_cm.addAction('Previous bookmark', self.edit_book.bookmark_prev_cb, 'Alt+PgUp')
		self.m_cm.addAction('Next bookmark', self.edit_book.bookmark_next_cb, 'Alt+PgDown')
		self.m_cm.addSeparator()
		self.cm_actionGroup = QActionGroup(self, triggered=self.codemark_go)

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

	def create_toolbar(self):
		self.toolbar = self.addToolBar('Toolbar')
		self.toolbar.setIconSize(QSize(16,16))
		self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)

		si = QApplication.style().standardIcon
		#(QStyle.SP_DirClosedIcon)

		# exit
		self.toolbar.addAction(si(QStyle.SP_TitleBarCloseButton), 'Quit', self.close)

		# edit related
		# if need editing support
		if self.inner_editing:
			self.toolbar.addSeparator()
			self.toolbar.addAction(si(QStyle.SP_DialogSaveButton), 'Save', self.edit_book.save_current_page)
			self.toolbar.addSeparator()
			self.toolbar.addAction(QIcon('icons/undo.png'), 'Undo', self.edit_book.undo_edit_cb)
			self.toolbar.addAction(QIcon('icons/redo.png'), 'Redo', self.edit_book.redo_edit_cb)
			self.toolbar.addSeparator()
			self.toolbar.addAction(QIcon('icons/cut.png'), 'Cut', self.edit_book.cut_edit_cb)
			self.toolbar.addAction(QIcon('icons/copy.png'), 'Copy', self.edit_book.copy_edit_cb)
			self.toolbar.addAction(QIcon('icons/paste.png'), 'Paste', self.edit_book.paste_edit_cb)
			self.toolbar.addSeparator()
			self.toolbar.addAction(QIcon('icons/find-replace.png'), 'Find & Replace', self.edit_book.find_cb)

		# find 
		self.toolbar.addSeparator()
		self.toolbar.addAction(si(QStyle.SP_FileDialogContentsView), 'Find', self.edit_book.find_cb)
		self.toolbar.addAction(si(QStyle.SP_ArrowDown), 'Find Next', self.edit_book.find_next_cb)
		self.toolbar.addAction(si(QStyle.SP_ArrowUp), 'Find Previous', self.edit_book.find_prev_cb)
		self.toolbar.addSeparator()
		# goto
		self.toolbar.addAction(QIcon('icons/go-jump.png'), 'Go to line', self.edit_book.goto_line_cb)
		self.toolbar.addSeparator()

		# code view
		self.toolbar.addAction(si(QStyle.SP_FileDialogListView), 'Search ctags', self.go_search_ctags_cb)
		self.toolbar.addAction(si(QStyle.SP_FileDialogDetailedView), 'Search file list', self.go_search_file_list_cb)
		self.toolbar.addSeparator()
		self.toolbar.addAction(si(QStyle.SP_MediaSeekBackward), 'Previous Result', self.go_prev_res_cb)
		self.toolbar.addAction(si(QStyle.SP_MediaSeekForward), 'Next Result', self.go_next_res_cb)
		self.toolbar.addSeparator()
		self.toolbar.addAction(si(QStyle.SP_MediaSkipBackward), 'Previous Position', self.go_prev_pos_cb)
		self.toolbar.addAction(si(QStyle.SP_MediaSkipForward), 'Next Position', self.go_next_pos_cb)
		self.toolbar.addSeparator()
		self.code_ctx_view_act = self.toolbar.addAction(QIcon('icons/codeview.png'), 'Code Quick View', self.code_ctx_view_act_cb)
		self.code_ctx_view_act.setCheckable(True)
		self.code_ctx_view_act.setChecked(self.is_show_code_ctx_view)
	
		
	# app config
	def app_get_config_file(self):
		config_file = '~/.seascoperc'
		return os.path.expanduser(config_file)

	def app_read_config(self):
		self.recent_projects = []
		self.app_style = None
		self.app_font = None
		self.ev_font = None
		self.exit_dont_ask = False
		self.inner_editing_conf = False
		self.inner_editing = False
		self.is_show_toolbar = False
		self.is_show_code_ctx_view = False
		self.edit_ext_cmd = 'x-terminal-emulator -e vim %F +%L'
		self.eb_is_show_line = False

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
				self.ev_font = line[1].split('\n')[0]
			if (key == 'edit_show_line_num'):
				if ('true' == line[1].split('\n')[0]):
					self.eb_is_show_line = True
			if (key == 'show_toolbar'):
				if ('true' == line[1].split('\n')[0]):
					self.is_show_toolbar = True
				else:
					self.is_show_toolbar = False
			if (key == 'edit_ext_cmd'):
				self.edit_ext_cmd = line[1]
			if (key == 'exit_dont_ask'):
				if ('true' == line[1].split('\n')[0]):
					self.exit_dont_ask = True
			if (key == 'inner_editing'):
				if ('true' == line[1].split('\n')[0]):
					self.inner_editing_conf = True
				else:
					self.inner_editing_conf = False
			if os.getenv("SEASCOPE_EDIT"):
				self.inner_editing = True
			else:
				self.inner_editing = self.inner_editing_conf
		cf.close()

	def app_write_config(self):
		cf = open(self.app_get_config_file(), 'w')
		cf.write('recent_projects' + '=' + string.join(self.recent_projects, ',')+ '\n')
		if (self.app_style):
			cf.write('app_style' + '=' + self.app_style + '\n')
		if (self.app_font):
			cf.write('app_font' + '=' + self.app_font + '\n')
		if (self.ev_font):
			cf.write('edit_font' + '=' + self.ev_font + '\n')
		if (self.inner_editing_conf):
			cf.write('inner_editing' + '=' + 'true' + '\n')
		else:
			cf.write('inner_editing' + '=' + 'false' + '\n')
		if (self.eb_is_show_line):
			cf.write('edit_show_line_num' + '=' + 'true' + '\n')
		if (self.is_show_toolbar):
			cf.write('show_toolbar' + '=' + 'true' + '\n')
		if (self.exit_dont_ask):
			cf.write('exit_dont_ask' + '=' + 'true' + '\n')
		if (self.edit_ext_cmd):
			cf.write('edit_ext_cmd' + '=' + self.edit_ext_cmd + '\n')
		cf.close()

	def app_gui_state_file(self):
		return os.path.expanduser('~/.seascopeguirc')

	def app_gui_state_read(self):
		f = self.app_gui_state_file()
		data = None
		try:
			if os.path.exists(f):
				with open(f, 'rb') as fp:
					import json
					data = json.load(fp)
		except Exception as e:
			print 'app_gui_state_read:', e
		return data

	def app_gui_state_write(self, data):
		f = self.app_gui_state_file()
		try:
			with open(f, 'wb') as fp:
				import json
				json.dump(data, fp)
		except Exception as e:
			print 'app_gui_state_write:', e

	def app_gui_get_geometry(self):
		rect = self.geometry()
		return (rect.x(), rect.y(), rect.width(), rect.height())
	
	def app_gui_set_geometry(self, geometry):
		x = geometry[0]
		y = geometry[1]
		w = geometry[2]
		h = geometry[3]
		self.setGeometry(x, y, w, h)

	def app_gui_state_save(self, proj_path):
		pd                    = {}
		pd ['file_line_list'] = self.edit_book.get_file_line_list()
		pd ['dir_view_list']  = self.file_view.get_dir_view_list()
		pd ['geometry']       = self.app_gui_get_geometry()

		try:
			data = self.app_gui_state_read()
			if data == None:
				data = {}
			if 'proj_gui_state' not in data:
				data['proj_gui_state'] = {}
			data['proj_gui_state'][proj_path] = pd
			self.app_gui_state_write(data)
		except Exception as e:
			print 'app_gui_state_save:', e

	def app_gui_state_restore(self, proj_path):
		try:
			data = self.app_gui_state_read()
			if data == None:
				return
			pgs = data.pop('proj_gui_state', {})
			pd = pgs.pop(proj_path, {})
			for fl in pd.pop('file_line_list', []):
				try:
					(f, l) = fl.rsplit(':', 1)
					l = int(l)
					if os.path.isabs(f) and f.startswith(proj_path) and os.path.isfile(f):
						self.edit_book.show_file_line(f, l, hist=False)
				except:
					pass
			for d in pd.pop('dir_view_list', []):
				if os.path.isabs(d) and f.startswith(proj_path) and os.path.isdir(d):
					self.file_view.open_dir_view(d)
			try:
				self.app_gui_set_geometry(pd ['geometry'])
			except Exception as e:
				print 'Geometry configuration not restored'
				
		except Exception as e:
			print 'app_gui_state_restore:', e
		
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
		self.qui.setup()

		self.editor_tab_changed_cb(None)
		proj_path = backend.proj_dir()
		self.update_recent_projects(proj_path)
		self.app_gui_state_restore(proj_path)

	def proj_new_cb(self):
		if backend.proj_is_open():
			if not DialogManager.show_proj_close():
				return
			self.proj_close_cb()

		dlg = BackendChooserDialog()
		bname = dlg.run_dialog()
		if bname == None:
			return

		proj_args = ProjectUi.show_settings_ui(bname, None)
		if not proj_args:
			return

		if not backend.proj_new(bname, proj_args):
			return
		# XXX FIXIT
		self.qui.do_rebuild()
		self.proj_new_or_open()

	def proj_open(self, proj_path):
		bl = backend.plugin_guess(proj_path)
		if len(bl) == 0:
			msg = "Project '%s': No backend is interested" % proj_path
			msg_box(msg)
			return
		proj_type = bl[0]
		if len(bl) > 1:
			msg = "Project '%s': Many backends interested" % proj_path
			for b in be:
				msg += '\n\t' + b.name()
			msg += '\n\nGoing ahead with: ' + proj_type
			msg_box(msg)
		print "Project '%s': using '%s' backend" % (proj_path, proj_type)

		rc = backend.proj_open(proj_path, proj_type)
		if not rc:
			print 'proj_open', proj_path, 'failed'
			return

		self.proj_new_or_open()

	def proj_open_cb(self):
		proj_path = DialogManager.show_project_open_dialog(self.recent_projects)
		if proj_path != None:
			if backend.proj_is_open():
				self.proj_close_cb()

			self.proj_open(proj_path)

	def proj_close_cb(self):
		proj_path = backend.proj_dir()
		self.update_recent_projects(proj_path)
		self.app_gui_state_save(proj_path)
		self.setWindowTitle("Seascope")

		backend.proj_close()
		self.qui.reset()

		if self.inner_editing:
			self.edit_book.close_all_cb()
		else:
			self.edit_book.clear()

		self.res_book.clear()
		self.file_view.clear()
		self.cm_mgr.clear()
		self.code_ctx_view.clear()

	def proj_settings_cb(self):
		proj_args = backend.proj_settings_get()
		proj_args = ProjectUi.show_settings_ui(backend.proj_type(), proj_args)
		if proj_args:
			backend.proj_settings_update(proj_args)

	def editor_tab_changed_cb(self, fname):
		#title = backend.proj_name()
		prj_dir = backend.proj_dir()
		if prj_dir:
			parent = prj_dir
			home_dir = os.path.expanduser('~')
			for i in range(2):
				parent = os.path.dirname(parent)
				if parent == home_dir:
					break
			title = os.path.relpath(prj_dir, parent)
		if not prj_dir:
			title = 'Seascope'
		if fname and fname != '':
			fname = str(fname)
			#if fname.startswith(prj_dir):
				#fname = os.path.relpath(fname, prj_dir)
			title = title + ' - ' + fname
		else:
			fname = 'Seascope'
			title = title + ' - ' + fname
		self.setWindowTitle(title)

	def show_file_line(self, filename, line):
		self.edit_book.show_file_line(filename, line)

	def show_toolbar_cb(self):
		self.is_show_toolbar = self.show_toolbar.isChecked()
		if self.is_show_toolbar:
			self.create_toolbar()
		else:
			self.removeToolBar(self.toolbar)

	def code_ctx_view_act_cb(self):
		self.is_show_code_ctx_view = self.code_ctx_view_act.isChecked()
		if self.is_show_code_ctx_view:
			self.code_ctx_view.show()
		else:
			self.code_ctx_view.hide()

	def connect_signals(self):
		self.edit_book.sig_history_update.connect(self.res_book.history_update)
		self.edit_book.sig_tab_changed.connect(self.editor_tab_changed_cb)
		self.res_book.sig_show_file_line.connect(self.edit_book.show_file_line)
		self.file_view.sig_show_file.connect(self.edit_book.show_file)
		self.edit_book.sig_open_dir_view.connect(self.file_view.open_dir_view)
		self.edit_book.sig_file_closed.connect(self.codemark_del_file_cb)
		self.edit_book.sig_editor_text_selected.connect(self.editor_text_selected)
		self.code_ctx_view.sig_codecontext_showfile.connect(self.code_context_showfile_cb)
		
	def editor_text_selected(self, text):
		if self.is_show_code_ctx_view:
			if not self.code_ctx_view.set_cur_query(text):
				return
			rquery = {}
			rquery['cmd'] = 'DEF'
			rquery['req'] = str(text)
			rquery['opt'] = None
			sig_res = backend.prj.qry.query(rquery)
			sig_res[0].connect(self.code_ctx_view_query_res_cb)

	def code_ctx_view_query_res_cb(self, sym, res):
		self.code_ctx_view.showResult(sym, res)
	
	def code_context_showfile_cb(self, filename, line):
		self.show_file_line(filename, line)

	def setup_widget_tree(self):
		self.hsp = QSplitter();
		self.hsp.addWidget(self.edit_book)
		self.hsp.addWidget(self.file_view)
		self.hsp.setSizes([700, 1])

		self.vsp = QSplitter();
		self.vsp.setOrientation(Qt.Vertical)
		self.vsp.addWidget(self.hsp)
		self.vsp.addWidget(self.res_book)
		self.hsp_res = QSplitter();
		self.hsp_res.addWidget(self.res_book)
		self.hsp_res.addWidget(self.code_ctx_view)
		self.vsp.addWidget(self.hsp_res)
		
		self.hsp_res.setSizes([200, 1])
		self.vsp.setSizes([1, 60])
		
		self.setCentralWidget(self.vsp)
		self.setWindowTitle('Seascope')
		self.setGeometry(300, 100, 800, 600)
		#self.showMaximized()

		QApplication.setWindowIcon(QIcon('icons/seascope.svg'))

		# update checked menu item
		self.edit_book.is_show_line = self.eb_is_show_line
		self.edit_book.m_show_line_num.setChecked(self.edit_book.is_show_line)
		if (self.ev_font):
			self.edit_book.ev_font = self.ev_font
			self.code_ctx_view.ev_font = self.ev_font
		self.show_toolbar.setChecked(self.is_show_toolbar)

	def create_widgets(self):
		self.qui_h = QueryUiHelper()
		self.qui = QueryUi(self.qui_h)

		if self.inner_editing:
			self.edit_book = EdViewRW.EditorBookRW()
		else:
			self.edit_book = EdView.EditorBook()

		self.res_book  = ResView.ResultManager()
		self.file_view = FileView.FileTree()
		self.cm_mgr    = CodemarkView.CodemarkManager()
		self.code_ctx_view = CodeContextView.CodeContextViewManager()
		self.code_ctx_view.hide()

		self.sbar = self.statusBar()
		self.create_mbar()
		
		if self.is_show_toolbar:
			self.create_toolbar()

	def setup_widget_hints(self):
		if self.inner_editing:
			EdViewRW.EditorView.ev_popup = self.backend_menu
		else:
			EdView.EditorView.ev_popup = self.backend_menu

		CallView.CallTreeWindow.parent = self
		ClassGraphView.ClassGraphWindow.parent = self
		FileFuncGraphView.FileFuncGraphWindow.parent = self

		self.qui.set_backend_menu(self.backend_menu)
		self.qui_h.edit_book = self.edit_book
		self.qui_h.res_book = self.res_book
		self.qui_h.call_view = CallView
		self.qui_h.class_graph_view = ClassGraphView
		self.qui_h.file_func_graph_view = FileFuncGraphView
		self.qui_h.dbg_view = DebugView
		self.qui_h.file_view = self.file_view

	def setup_style_and_font(self):
		if self.app_style:
			QApplication.setStyle(self.app_style)
		if self.app_font:
			font = QFont()
			font.fromString(self.app_font)
			QApplication.setFont(font)

	def __init__(self, parent=None, app_start_dir=None):
		QMainWindow.__init__(self)
		self.seascope_start_dir = app_start_dir

		self.app_read_config()

		self.create_widgets()
		self.setup_widget_hints()
		self.connect_signals()
		self.setup_widget_tree()
		self.setup_style_and_font()

		prj_path = None
		args = QApplication.arguments()
		if len(args) == 2:
			prj_path = str(args[1])
			if not os.path.isabs(prj_path):
				dname = self.seascope_start_dir
				prj_path = os.path.join(dname, prj_path)
			
		if not prj_path or os.getenv('SEASCOPE_RESTART_HINT'):
			if len(self.recent_projects):
				prj_path = self.recent_projects[0]
		if prj_path:
			self.proj_open(prj_path)
		#else:
			#self.proj_open_cb()
		self.file_restarted_cb()

if __name__ == "__main__":

	# pyqt version 4.5 is required
	pyqt_required_version = 0x40500 
	if not QtCore.PYQT_VERSION >= pyqt_required_version:
		print 'Needs pyqt version > 4.5'
		sys.exit(-1)

	# change working dir to the script dir so that we can run this script anywhere else
	app_start_dir = os.getcwd()
	app_dir = os.path.dirname(os.path.realpath(__file__))
	os.chdir(app_dir)
	
	# load plugins
	backend.load_plugins()
	view.load_plugins()

	# start app
	app = QApplication(sys.argv)
	ma = SeascopeApp(app_start_dir=app_start_dir)
	ma.show()
	ret = app.exec_()
	sys.exit(ret)
