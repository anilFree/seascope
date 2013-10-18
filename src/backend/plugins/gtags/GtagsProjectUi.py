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

from ..PluginBase import ProjectBase, ConfigBase, QueryBase, QueryDialogBase
from ..PluginBase import QueryUiBase
from .. import PluginBase, PluginHelper


cmd_table = [
	[	['REF',	'-r'],	['&References',		'Ctrl+0'],	['References to'	]	],
	[	['DEF',	''],	['&Definitions',	'Ctrl+1'],	['Definition of'	]	],
	#[	['<--',	'2'],	['&Called Functions',	'Ctrl+2'],	['Functions called by'	]	],
	[	['-->',	'-r'],	['C&alling Functions',	'Ctrl+3'],	['Functions calling'	]	],
	#[	['TXT',	'4'],	['Find &Text',		'Ctrl+4'],	['Find text'		]	],
	[	['GREP','-g'],	['Find &Egrep',		'Ctrl+5'],	['Find egrep pattern'	]	],
	[	['FIL',	'-P'],	['Find &File',		'Ctrl+7'],	['Find files'		]	],
	[	['INC',	'-g'],	['&Include/Import',	'Ctrl+8'],	['Find include/import'	]	],
	[	['---', None],	[None				]					],
	[	['QDEF', ''],	['&Quick Definition',	'Ctrl+]'],	[None			]	],
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
		
class GtagsQueryDialog(QueryDialogBase):
	def __init__(self):
		QueryDialogBase.__init__(self, 'Gtags Query', cmd_qstrlist)
		self.cmd_qstr2str = cmd_qstr2str
		self.cmd_str2qstr = cmd_str2qstr

	def query_dlg_cb(self, req, cmd_str):
		if req != '' and self.qd_substr_chkbox.isChecked():
			req = '.*' + req + '.*'
		opt = None
		if self.qd_icase_chkbox.isChecked():
			opt = '-i'
		res = (cmd_str, req, opt)
		return res

def show_msg_dialog(msg):
	QMessageBox.warning(None, "Seascope", msg, QMessageBox.Ok)

class QueryUiGtags(QueryUiBase):
	def __init__(self, qry):
		self.menu_cmd_list = menu_cmd_list
		QueryUiBase.__init__(self)
		self.query = qry
		self.query_dlg = GtagsQueryDialog()
		self.ctree_args = ctree_query_args

	def prepare_menu(self):
		QueryUiBase.prepare_menu(self)
		menu = PluginHelper.backend_menu
		menu.setTitle('G&tags')

	@staticmethod
	def prj_show_settings_ui(proj_args):
		dlg = ProjectSettingsGtagsDialog()
		return dlg.run_dialog(proj_args)

class ProjectSettingsGtagsDialog(QDialog):
	def __init__(self):
		QDialog.__init__(self)

		self.ui = uic.loadUi('ui/project_settings.ui', self)

	def run_dialog(self, proj_args):
		self.pi_path_lbl.setText(proj_args[0])
		self.pi_type_lbl.setText('GNU global/gtags')
		self.exec_()
		return proj_args
