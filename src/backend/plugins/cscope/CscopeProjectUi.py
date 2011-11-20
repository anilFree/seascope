import os
import sys
import re

from PyQt4 import QtGui, QtCore, uic

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import DialogManager

from ..PluginBase import ProjectBase, ConfigBase, QueryBase
from ..PluginBase import QueryUiBase

def show_msg_dialog(msg):
	QMessageBox.warning(None, "SeaScope", msg, QMessageBox.Ok)

def get_cscope_files_list(rootdir):
	file_list = []
	if (not os.path.isdir(rootdir)):
		print "Not a directory:", rootdir
		return file_list
	for root, subFolders, files in os.walk(rootdir):
		for f in files:
			f = os.path.join(root, f)
			if (re.search('\.(h|c|H|C|hh|cc|hpp|cpp|hxx|cxx||l|y|s|S|pl|pm|java)$', f) != None):
				file_list.append(f)
	return file_list

class QueryUiCscope(QueryUiBase):
	parent = None

	def __init__(self, qry):
		QueryUiBase.__init__(self)
		self.query = qry

	#def ctree_show_file_line(self, filename, line):
		#self.raise_()
		#self.activateWindow()
		#self.edit_book.show_file_line(filename, line)

	def do_cs_query_ctree(self, cmd_id, req, opt):
		ctree_query_args = [
			[3, '--> F', 'Calling tree'		],
			[2, 'F -->', 'Called tree'		],
			[0, '==> F', 'Advanced calling tree'	],
		]
		QueryUiBase.call_view.create_page(req, self.query.cs_query, ctree_query_args)
		
	def do_cs_query(self, cmd_id, req, opt):
		## create page
		cmd_dict = {
			0: 'REF',
			1: 'DEF',
			2: '<--',
			3: '-->',
			4: 'TXT',
			5: 'GRP',
			7: 'FIL',
			8: 'INC',
		}
		name = cmd_dict[cmd_id] + ' ' + req
		page = QueryUiBase.res_book.create_result_page(name)
		## add result
		sig_res = self.query.cs_query(cmd_id, req, opt)
		sig_res[0].connect(page.add_result)
		#page.add_result(req, res)
		QueryUiCscope.dbg_mgr.connect_to_cs_sig_res(sig_res[1])

	def cs_query_cb(self, cmd_id):
		if (not self.query.cs_is_open()):
			return
		if (not self.query.cs_is_ready()):
			DialogManager.show_msg_dialog('\nProject has no source files')
			return
		req = QueryUiBase.edit_book.get_current_word()
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
		sig_rebuild = self.query.cs_rebuild()
		dlg = QProgressDialog()
		dlg.setWindowTitle('SeaScope rebuild')
		dlg.setLabelText('Rebuilding cscope database...')
		dlg.setCancelButton(None)
		dlg.setMinimum(0)
		dlg.setMaximum(0)
		sig_rebuild.connect(dlg.accept)
		while dlg.exec_() != QDialog.Accepted:
			pass

	def prepare_menu(self):
		menu = QueryUiBase.backend_menu
		menu.setTitle('&Cscope')
		#menu.setFont(QFont("San Serif", 8))
		menu.addAction('&References',		self.cb_ref,	'Ctrl+0')
		menu.addAction('&Definitions',		self.cb_def, 	'Ctrl+1')
		menu.addAction('&Called Functions',	self.cb_called, 'Ctrl+2')
		menu.addAction('C&alling Functions',	self.cb_calling,'Ctrl+3')
		menu.addAction('Find &Text',		self.cb_text, 	'Ctrl+4')
		menu.addAction('Find &Egrep',		self.cb_egrep, 	'Ctrl+5')
		menu.addAction('Find &File',		self.cb_file, 	'Ctrl+7')
		menu.addAction('&Including Files',	self.cb_inc, 	'Ctrl+8')
		menu.addSeparator()
		menu.addAction('&Quick Definition',	self.cb_quick_def,'Ctrl+]')
		menu.addAction('Call Tr&ee',		self.cb_call_tree,'Ctrl+\\')
		menu.addSeparator()
		menu.addAction('Re&build Database',	self.cb_rebuild)

	def cs_qdef_result(self, req, res):
		count = len(res)
		if count > 1:
			page = QueryUiBase.res_book.create_result_page_single()
			page.add_result(req, res)
			
			dlg = QDialog()
			dlg.setWindowTitle('Quick Definition: ' + req)
			vlay = QVBoxLayout(dlg)
			vlay.addWidget(page)

			page.sig_show_file_line.connect(QueryUiBase.edit_book.show_file_line)
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
		sig_res = self.query.cs_query(cmd_id, req, opt)
		sig_res[0].connect(self.cs_qdef_result)
		QueryUiCscope.dbg_mgr.connect_to_cs_sig_res(sig_res[1])

	@staticmethod
	def set_edit_book(book):
		QueryBase.edit_book = book

	@staticmethod
	def prj_show_settings_ui(proj_args):
		dlg = ProjectSettingsCscopeDialog()
		return dlg.run_dialog(proj_args)

class ProjectSettingsCscopeDialog(QObject):
	def __init__(self):
		QObject.__init__(self)

		self.dlg = uic.loadUi('ui/proj_new.ui')
		self.dlg.pd_path_tbtn.setIcon(QFileIconProvider().icon(QFileIconProvider.Folder))

		self.dlg.pd_src_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

		QObject.connect(self.dlg.pd_path_tbtn, SIGNAL("clicked()"), self.path_open_cb)
		QObject.connect(self.dlg.pd_add_btn, SIGNAL("clicked()"), self.src_add_cb)
		QObject.connect(self.dlg.pd_rem_btn, SIGNAL("clicked()"), self.src_rem_cb)
		QObject.connect(self.dlg, SIGNAL("accepted()"), self.ok_btn_cb)

	def path_open_cb(self):
                fdlg = QFileDialog(None, "Choose directory")
		fdlg.setFileMode(QFileDialog.Directory);
		fdlg.setDirectory(self.dlg.pd_path_inp.text())
		if (fdlg.exec_()):
			path_dir = fdlg.selectedFiles()[0];
			self.dlg.pd_path_inp.setText(str(path_dir))

	def src_add_cb(self):
                fdlg = QFileDialog(None, "Choose directory")
		fdlg.setFileMode(QFileDialog.Directory);
		fdlg.setDirectory(self.dlg.pd_path_inp.text())
		if (fdlg.exec_()):
			d = fdlg.selectedFiles()[0];
			d = str(d)
			d = d.strip()
			if (d == None):
				return
			d = os.path.normpath(d)
			if (d == '' or not os.path.isabs(d)):
				return
			self.src_add_files(d)

	def src_rem_cb(self):
		li = self.dlg.pd_src_list
		for item in li.selectedItems():
			row = li.row(item)
			li.takeItem(row)

	def src_add_files(self, src_dir):
		file_list = get_cscope_files_list(src_dir)
		self.dlg.pd_src_list.addItems(file_list)

	def ok_btn_cb(self):
		proj_dir = os.path.join(str(self.dlg.pd_path_inp.text()), str(self.dlg.pd_name_inp.text()))
		proj_dir = os.path.normpath(proj_dir)
		if (self.is_new_proj):
			if (proj_dir == '' or not os.path.isabs(proj_dir)):
				return
			if (os.path.exists(proj_dir)):
				show_msg_dialog("\nProject already exists")
				return
			os.mkdir(proj_dir)
		# File list
		cs_list = []
		for inx in range(self.dlg.pd_src_list.count()):
			val = str(self.dlg.pd_src_list.item(inx).text())
			cs_list.append(val)
		cs_list = list(set(cs_list))
		# Cscope opt
		cs_opt = []
		if self.dlg.pd_invert_chkbox.isChecked():
			cs_opt.append('-q')
		if self.dlg.pd_kernel_chkbox.isChecked():
			cs_opt.append('-k')

		self.res = [proj_dir, cs_opt, cs_list]

	def set_proj_args(self, proj_args):
		(proj_dir, cs_opt, cs_list) = proj_args
		(proj_base, proj_name) = os.path.split(proj_dir)
		self.dlg.pd_path_inp.setText(proj_base)
		self.dlg.pd_name_inp.setText(proj_name)
		# File list
		fl = cs_list
		self.dlg.pd_src_list.addItems(fl)
		# Cscope opt
		for opt in cs_opt:
			if (opt == '-q'):
				self.dlg.pd_invert_chkbox.setChecked(True)
			if (opt == '-k'):
				self.dlg.pd_kernel_chkbox.setChecked(True)

	def run_dialog(self, proj_args):
		self.dlg.pd_src_list.clear()
		if (proj_args == None):
			self.is_new_proj = True
			self.dlg.pd_invert_chkbox.setChecked(True)
		else:
			self.is_new_proj = False
			self.set_proj_args(proj_args)
		self.res = None
		
		self.dlg.pd_path_frame.setEnabled(self.is_new_proj)

		while True:
			ret = self.dlg.exec_()
			if (ret == QDialog.Accepted or ret == QDialog.Rejected):
				break
		return self.res
