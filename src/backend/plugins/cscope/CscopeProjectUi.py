# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os
import sys
import re

from PyQt4 import QtGui, QtCore, uic

from PyQt4.QtGui import *
from PyQt4.QtCore import *

from ..PluginBase import ProjectBase, ConfigBase, QueryBase
from ..PluginBase import QueryUiBase
from .. import PluginBase, PluginHelper


cmd_table = [
	[	['REF',	'0'],	['&References',		'Ctrl+0'],	['References to'	]	],
	[	['DEF',	'1'],	['&Definitions',	'Ctrl+1'],	['Definition of'	]	],
	[	['<--',	'2'],	['&Called Functions',	'Ctrl+2'],	['Functions called by'	]	],
	[	['-->',	'3'],	['C&alling Functions',	'Ctrl+3'],	['Functions calling'	]	],
	[	['TXT',	'4'],	['Find &Text',		'Ctrl+4'],	['Find text'		]	],
	[	['GREP','5'],	['Find &Egrep',		'Ctrl+5'],	['Find egrep pattern'	]	],
	[	['FIL',	'7'],	['Find &File',		'Ctrl+7'],	['Find files'		]	],
	[	['INC',	'8'],	['&Including Files',	'Ctrl+8'],	['Find #including'	]	],
	[	['---', None],	[None				]					],
	[	['QDEF', '11'], ['&Quick Definition',	'Ctrl+]'],	[None			]	],
	[	['CTREE','12'],	['Call Tr&ee',		'Ctrl+\\'],	['Call tree'		]	],
	[	['---', None],	[None				],					],
	[	['CLGRAPH', '13'],  ['Class &Graph',	'Ctrl+:'],	['Class graph'		]	],
	[	['CLGRAPHD', '14'], ['Class Graph Dir',	'Ctrl+;'],	['Class graph dir'	]	],
	[	['FFGRAPH', '14'], ['File Func Graph',	'Ctrl+^'],	['File Func graph dir'	]	],
	[	['---', None],	[None				],					],
	[	['UPD', '25'],	['Re&build Database',	None	],	[None			]	],
]

menu_cmd_list = [ [c[0][0]] + c[1] for c in cmd_table ]
cmd_str2id = {}
cmd_str2qstr = {}
cmd_qstr2str = {}
for c in cmd_table:
	if c[0][1] != None:
		cmd_str2id[c[0][0]] = c[0][1]
		cmd_str2qstr[c[0][0]] = c[2][0]
		cmd_qstr2str[c[2][0]] = c[0][0]
# python 2.7
#cmd_str2id = { c[0][0]:c[0][1] for c in cmd_table if c[0][1] != None }
#cmd_str2qstr = { c[0][0]:c[2][0] for c in cmd_table if c[0][1] != None }
#cmd_qstr2str = { c[2][0]:c[0][0] for c in cmd_table if c[0][1] != None }
cmd_qstrlist = [ c[2][0] for c in cmd_table if c[0][1] != None and c[2][0] != None ]

ctree_query_args = [
	['-->',	'--> F', 'Calling tree'			],
	['<--',	'F -->', 'Called tree'			],
	['REF',	'==> F', 'Advanced calling tree'	],
]
		
class CscopeQueryDialog(QueryDialogBase):
	def __init__(self):
		QueryDialogBase.__init__(self, 'Cscope Query', cmd_qstrlist)
		self.cmd_qstr2str = cmd_qstr2str
		self.cmd_str2qstr = cmd_str2qstr

	def query_dlg_cb(self, req, cmd_str):
		if req != '' and self.qd_substr_chkbox.isChecked():
			req = '.*' + req + '.*'
		opt = None
		if self.qd_icase_chkbox.isChecked():
			opt = '-C'
		res = (cmd_str, req, opt)
		return res

def show_msg_dialog(msg):
	QMessageBox.warning(None, "Seascope", msg, QMessageBox.Ok)

def dir_scan_csope_files(rootdir):
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
		self.menu_cmd_list = menu_cmd_list
		QueryUiBase.__init__(self)
		self.query = qry
		self.query_dlg = CscopeQueryDialog()
		self.ctree_args = ctree_query_args

	def prepare_menu(self):
		QueryUiBase.prepare_menu(self)
		menu = PluginHelper.backend_menu
		menu.setTitle('&Cscope')

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
		file_list = dir_scan_csope_files(src_dir)
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
