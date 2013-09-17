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
	[	['REF',	''],	['&References',		'Ctrl+0'],	['References to'	]	],
	[	['DEF',	''],	['&Definitions',	'Ctrl+1'],	['Definition of'	]	],
	#[	['<--',	'2'],	['&Called Functions',	'Ctrl+2'],	['Functions called by'	]	],
	[	['-->',	'3'],	['C&alling Functions',	'Ctrl+3'],	['Functions calling'	]	],
	#[	['TXT',	'4'],	['Find &Text',		'Ctrl+4'],	['Find text'		]	],
	[	['GREP',''],	['Find &Egrep',		'Ctrl+5'],	['Find egrep pattern'	]	],
	[	['FIL',	''],	['Find &File',		'Ctrl+7'],	['Find files'		]	],
	[	['INC',	'8'],	['&Include/Import',	'Ctrl+8'],	['Find include/import'	]	],
	[	['---', None],	[None				]					],
	[	['QDEF', ''], ['&Quick Definition',	'Ctrl+]'],	[None			]	],
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
	#['<--',	'F -->', 'Called tree'			],
	['REF',	'==> F', 'Advanced calling tree'	],
]
		
clgraph_query_args = [
	['CLGRAPH',	'D', 'Derived classes'			],
	['CLGRAPH',	'B', 'Base classes'			],
]

ffgraph_query_args = [
	['FFGRAPH',    'F',   'File functions graph'],
	['FFGRAPH_E',  'F+E', 'File functions + external graph'],
	['FFGRAPH_D',  'D',   'Directory functions graph'],
	['FFGRAPH_DE', 'D+E', 'Directory functions + external graph']
]

		
class QueryDialog(QDialog):
	dlg = None

	def __init__(self):
		QDialog.__init__(self)

		self.ui = uic.loadUi('backend/plugins/idutils/ui/id_query.ui', self)
		self.qd_sym_inp.setAutoCompletion(False)
		self.qd_sym_inp.setInsertPolicy(QComboBox.InsertAtTop)
		self.qd_cmd_inp.addItems(cmd_qstrlist)

	def run_dialog(self, cmd_str, req):
		s = cmd_str2qstr[cmd_str]
		inx = self.qd_cmd_inp.findText(s)
		self.qd_cmd_inp.setCurrentIndex(inx)
		if (req == None):
			req = ''
		self.qd_sym_inp.setFocus()
		self.qd_sym_inp.setEditText(req)
		self.qd_sym_inp.lineEdit().selectAll()
		self.qd_substr_chkbox.setChecked(False)
		self.qd_icase_chkbox.setChecked(False)

		self.show()
		if (self.exec_() == QDialog.Accepted):
			req = str(self.qd_sym_inp.currentText())
			s = str(self.qd_cmd_inp.currentText())
			cmd_str = cmd_qstr2str[s]
			#self.qd_sym_inp.addItem(req)
			opt = []
			if cmd_str != 'TXT' and req != '' and self.qd_substr_chkbox.isChecked():
				opt.append('substring')
				if cmd_str == 'FIL':
					req = '*' + req + '*'
				else:
					req = '.*' + req + '.*'
			if (self.qd_icase_chkbox.isChecked()):
				opt.append('ignorecase')
			res = (cmd_str, req, opt)
			return res
		return None

	@staticmethod
	def show_dlg(cmd_str, req):
		if (QueryDialog.dlg == None):
			QueryDialog.dlg = QueryDialog()
		return QueryDialog.dlg.run_dialog(cmd_str, req)

def show_msg_dialog(msg):
	QMessageBox.warning(None, "Seascope", msg, QMessageBox.Ok)

class QueryUiIdutils(QueryUiBase):
	def __init__(self, qry):
		self.menu_cmd_list = menu_cmd_list
		QueryUiBase.__init__(self)
		self.query = qry
		self.ctree_args = ctree_query_args
		self.clgraph_args = clgraph_query_args
		self.ffgraph_args = ffgraph_query_args

	def query_cb(self, cmd_str):
		if (not self.query.id_is_open()):
			return
		if (not self.query.id_is_ready()):
			show_msg_dialog('\nProject has no source files')
			return
		if cmd_str == 'CLGRAPHD':
			f = PluginHelper.editor_current_file()
			if f:
				d = os.path.dirname(f)
				self.query_class_graph_dir(d)
			return
		if cmd_str == 'FFGRAPH':
			f = PluginHelper.editor_current_file()
			if f:
				self.query_file_func_graph(f)
			return
		req = PluginHelper.editor_current_word()
		if (req != None):
			req = str(req).strip()
		opt = None
		if cmd_str not in [ 'QDEF' ]:
			val = QueryDialog.show_dlg(cmd_str, req)
			if (val == None):
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

	def prepare_menu(self):
		QueryUiBase.prepare_menu(self)
		menu = PluginHelper.backend_menu
		menu.setTitle('&Idutils')

	@staticmethod
	def prj_show_settings_ui(proj_args):
		dlg = ProjectSettingsIdutilsDialog()
		return dlg.run_dialog(proj_args)

class ProjectSettingsIdutilsDialog(QDialog):
	def __init__(self):
		QDialog.__init__(self)

		self.ui = uic.loadUi('ui/project_settings.ui', self)

	def run_dialog(self, proj_args):
		self.pi_path_lbl.setText(proj_args[0])
		self.pi_type_lbl.setText('idutils')
		self.exec_()
		return proj_args
