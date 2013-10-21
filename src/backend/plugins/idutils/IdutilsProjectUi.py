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


def show_msg_dialog(msg):
	QMessageBox.warning(None, "Seascope", msg, QMessageBox.Ok)

class QueryUiIdutils(QueryUiBase):
	def __init__(self, qry):
		QueryUiBase.__init__(self)

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
