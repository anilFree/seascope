import os
import sys
import re

from PyQt4 import QtGui, QtCore, uic

from PyQt4.QtGui import *
from PyQt4.QtCore import *

import DialogManager

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

class ProjectDialog(QObject):
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

	def src_add_dir(self, d):
		file_list = get_cscope_files_list(d)
		self.dlg.pd_src_list.adddItems(file_list)

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
		self.dlg.pd_src_list.addItems(cs_list)
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


def show_project_dialog(proj_args):
	dlg = ProjectDialog()
	return dlg.run_dialog(proj_args)
