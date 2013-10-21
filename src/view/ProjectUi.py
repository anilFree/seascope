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

class ProjectSettingsDialog(QDialog):
	def __init__(self):
		QDialog.__init__(self)

		self.ui = uic.loadUi('ui/project_settings.ui', self)

	def run_dialog(self, prj_type, prj_args):
		if prj_args:
			prj_dir = prj_args[0]
			self.pi_type_lbl.setText(prj_type)
			self.pi_path_lbl.setText(prj_dir)
			self.exec_()
			return None
		fdlg = QFileDialog(None, "Choose source code directory")
		fdlg.setFileMode(QFileDialog.Directory);
		#fdlg.setDirectory(self.pd_path_inp.text())
		if fdlg.exec_():
			d = fdlg.selectedFiles()[0];
			d = str(d)
			if not d:
				return None
			d = os.path.normpath(d)
			if d == '' or not os.path.isabs(d):
				return None
			proj_args = [d, None, None]
			return proj_args
		return None

def show_settings_ui(prj_type, proj_args):
	dlg = None
	if prj_type == 'cscope':
		import CscopeProjectUi
		dlg = CscopeProjectUi.CscopeProjectSettingsDialog()
	else:
		dlg = ProjectSettingsDialog()
	return dlg.run_dialog(prj_type, proj_args)

