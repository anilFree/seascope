import os
import sys
import re

from PyQt4 import QtGui, QtCore, uic

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ..PluginBase import ProjectBase, ConfigBase, QueryBase
from ..PluginBase import QueryUiBase
from .. import PluginBase, PluginHelper

cmd_items = [
	'References to',
	'Definition of',
	'Functions called by',
	'Functions calling',
	'Find text',
	'Find egrep pattern',
	'Find files',
	'Find #including',
	'Call tree'
]

ctree_query_args = [
	[3, '--> F', 'Calling tree'		],
	[2, 'F -->', 'Called tree'		],
	[0, '==> F', 'Advanced calling tree'	],
]
		
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

#menu_cmd_list = [
#	[0,	'&References',		'Ctrl+0'],
#	[1,	'&Definitions',		'Ctrl+1'],
#	[2,	'&Called Functions',	'Ctrl+2'],
#	[3,	'C&alling Functions',	'Ctrl+3'],
#	[4,	'Find &Text',		'Ctrl+4'],
#	[5,	'Find &Egrep',		'Ctrl+5'],
#	[7,	'Find &File',		'Ctrl+7'],
#	[8,	'&Including Files',	'Ctrl+8'],
#	[None],
#	[11,	'&Quick Definition',	'Ctrl+]'],
#	[9,	'Call Tr&ee',		'Ctrl+\\'],
#	[None],
#	[-1,	'Re&build Database',	self.cb_rebuild],
#]

class QueryDialog(QDialog):
	dlg = None

	def __init__(self):
		QDialog.__init__(self)

		self.ui = uic.loadUi('backend/plugins/cscope/ui/cs_query.ui', self)
		self.cmd_items = [
			'References to',
			'Definition of',
			'Functions called by',
			'Functions calling',
			'Find text',
			'Find egrep pattern',
			'Find files',
			'Find #including',
			'Call tree'
		]
		self.qd_sym_inp.setAutoCompletion(False)
		self.qd_sym_inp.setInsertPolicy(QComboBox.InsertAtTop)
		self.qd_cmd_inp.addItems(self.cmd_items)

	def run_dialog(self, cmd_id, req):
		if (cmd_id > 5):
			cmd_id = cmd_id - 1
		self.qd_cmd_inp.setCurrentIndex(cmd_id)
		if (req == None):
			req = ''
		self.qd_sym_inp.setFocus()
		self.qd_sym_inp.setEditText(req)
		self.qd_sym_inp.lineEdit().selectAll()
		self.qd_substr_chkbox.setChecked(False)
		self.qd_icase_chkbox.setChecked(False)

		self.show()
		if (self.exec_() == QDialog.Accepted):
			cmd_id = self.qd_cmd_inp.currentIndex()
			if (cmd_id > 5):
				cmd_id = cmd_id + 1
			req = str(self.qd_sym_inp.currentText())
			#self.qd_sym_inp.addItem(req)
			if (req != '' and self.qd_substr_chkbox.isChecked()):
				req = '.*' + req + '.*'
			opt = None
			if (self.qd_icase_chkbox.isChecked()):
				opt = '-C'
			res = (cmd_id, req, opt)
			return res
		return None

	@staticmethod
	def show_dlg(cmd_id, req):
		if (QueryDialog.dlg == None):
			QueryDialog.dlg = QueryDialog()
		return QueryDialog.dlg.run_dialog(cmd_id, req)

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
	def __init__(self, qry):
		QueryUiBase.__init__(self)
		self.query = qry

	def do_cs_query_ctree(self, cmd_id, req, opt):
		ctree_query_args = [
			[3, '--> F', 'Calling tree'		],
			[2, 'F -->', 'Called tree'		],
			[0, '==> F', 'Advanced calling tree'	],
		]
		PluginHelper.call_view_page_new(req, self.query.cs_query, ctree_query_args)
		
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
		sig_res = self.query.cs_query(cmd_id, req, opt)
		PluginHelper.result_page_new(name, sig_res)

	def cs_query_cb(self, cmd_id):
		if (not self.query.cs_is_open()):
			return
		if (not self.query.cs_is_ready()):
			show_msg_dialog('\nProject has no source files')
			return
		req = PluginHelper.editor_current_word()
		if (req != None):
			req = str(req).strip()
		opt = None
		if (cmd_id < 10 or cmd_id == 12):
			val = QueryDialog.show_dlg(cmd_id, req)
			if (val == None):
				return
			(cmd_id, req, opt) = val
		if (req == None or req == ''):
			return
		if (cmd_id < 9):
			self.do_cs_query(cmd_id, req, opt)
		else:
			if cmd_id == 11:
				self.do_cs_query_qdef(1, req, opt)
			elif cmd_id == 9:
				self.do_cs_query_ctree(3, req, opt)
				
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

	def menu_cb(self, act):
		if act.cmd_id != -1:
			self.cs_query_cb(act.cmd_id)

	def prepare_menu(self):
		menu = PluginHelper.backend_menu
		menu.triggered.connect(self.menu_cb)
		menu.setTitle('&Cscope')
		#menu.setFont(QFont("San Serif", 8))
		menu_cmd_list = [
			[0,	'&References',		'Ctrl+0'],
			[1,	'&Definitions',		'Ctrl+1'],
			[2,	'&Called Functions',	'Ctrl+2'],
			[3,	'C&alling Functions',	'Ctrl+3'],
			[4,	'Find &Text',		'Ctrl+4'],
			[5,	'Find &Egrep',		'Ctrl+5'],
			[7,	'Find &File',		'Ctrl+7'],
			[8,	'&Including Files',	'Ctrl+8'],
			[None],
			[11,	'&Quick Definition',	'Ctrl+]'],
			[9,	'Call Tr&ee',		'Ctrl+\\'],
			[None],
			[-1,	'Re&build Database',	self.cb_rebuild],
		]
		for c in menu_cmd_list:
			if c[0] == None:
				menu.addSeparator()
				continue
			if c[0] == -1:
				act = menu.addAction(c[1], c[2])
			else:
				act = menu.addAction(c[1])
				act.setShortcut(c[2])
			act.cmd_id = c[0]

	def do_cs_query_qdef(self, cmd_id, req, opt):
		sig_res = self.query.cs_query(cmd_id, req, opt)
		PluginHelper.quick_def_page_new(sig_res)

	@staticmethod
	def prj_show_settings_ui(proj_args):
		dlg = ProjectSettingsCscopeDialog()
		return dlg.run_dialog(proj_args)

class ProjectSettingsCscopeDialog(QDialog):
	def __init__(self):
		QDialog.__init__(self)

		self.ui = uic.loadUi('backend/plugins/cscope/ui/cs_project_settings.ui', self)
		self.pd_path_tbtn.setIcon(QFileIconProvider().icon(QFileIconProvider.Folder))

		self.pd_src_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

		QObject.connect(self.pd_path_tbtn, SIGNAL("clicked()"), self.path_open_cb)
		QObject.connect(self.pd_add_btn, SIGNAL("clicked()"), self.src_add_cb)
		QObject.connect(self.pd_rem_btn, SIGNAL("clicked()"), self.src_rem_cb)
		QObject.connect(self, SIGNAL("accepted()"), self.ok_btn_cb)

	def path_open_cb(self):
                fdlg = QFileDialog(None, "Choose directory")
		fdlg.setFileMode(QFileDialog.Directory);
		fdlg.setDirectory(self.pd_path_inp.text())
		if (fdlg.exec_()):
			path_dir = fdlg.selectedFiles()[0];
			self.pd_path_inp.setText(str(path_dir))

	def src_add_cb(self):
                fdlg = QFileDialog(None, "Choose directory")
		fdlg.setFileMode(QFileDialog.Directory);
		fdlg.setDirectory(self.pd_path_inp.text())
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
		li = self.pd_src_list
		for item in li.selectedItems():
			row = li.row(item)
			li.takeItem(row)

	def src_add_files(self, src_dir):
		file_list = get_cscope_files_list(src_dir)
		self.pd_src_list.addItems(file_list)

	def ok_btn_cb(self):
		proj_dir = os.path.join(str(self.pd_path_inp.text()), str(self.pd_name_inp.text()))
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
		for inx in range(self.pd_src_list.count()):
			val = str(self.pd_src_list.item(inx).text())
			cs_list.append(val)
		cs_list = list(set(cs_list))
		# Cscope opt
		cs_opt = []
		if self.pd_invert_chkbox.isChecked():
			cs_opt.append('-q')
		if self.pd_kernel_chkbox.isChecked():
			cs_opt.append('-k')

		self.res = [proj_dir, cs_opt, cs_list]

	def set_proj_args(self, proj_args):
		(proj_dir, cs_opt, cs_list) = proj_args
		(proj_base, proj_name) = os.path.split(proj_dir)
		self.pd_path_inp.setText(proj_base)
		self.pd_name_inp.setText(proj_name)
		# File list
		fl = cs_list
		self.pd_src_list.addItems(fl)
		# Cscope opt
		for opt in cs_opt:
			if (opt == '-q'):
				self.pd_invert_chkbox.setChecked(True)
			if (opt == '-k'):
				self.pd_kernel_chkbox.setChecked(True)

	def run_dialog(self, proj_args):
		self.pd_src_list.clear()
		if (proj_args == None):
			self.is_new_proj = True
			self.pd_invert_chkbox.setChecked(True)
		else:
			self.is_new_proj = False
			self.set_proj_args(proj_args)
		self.res = None
		
		self.pd_path_frame.setEnabled(self.is_new_proj)

		while True:
			ret = self.exec_()
			if (ret == QDialog.Accepted or ret == QDialog.Rejected):
				break
		return self.res
