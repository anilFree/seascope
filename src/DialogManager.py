#!/usr/bin/env python

import sys
import os
import string

from PyQt4 import QtGui, QtCore, uic

from PyQt4.QtGui import *
from PyQt4.QtCore import *


def show_msg_dialog(msg):
	QMessageBox.information(None, "SeaScope", msg, QMessageBox.Ok)

def show_yes_no(msg):
	ret = QMessageBox.question(None, "SeaScope", msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
	return ret == QMessageBox.Yes

def show_proj_close():
	return show_yes_no("\nClose current project?")

class ProjectOpenDialog(QObject):
	def __init__(self):
		QObject.__init__(self)

		self.dlg = uic.loadUi('ui/proj_open.ui')
		self.dlg.pod_open_btn.setIcon(QFileIconProvider().icon(QFileIconProvider.Folder))

		QObject.connect(self.dlg.pod_open_btn, SIGNAL("clicked()"), self.open_btn_cb)
		QObject.connect(self.dlg, SIGNAL("accepted()"), self.ok_btn_cb)
		QObject.connect(self.dlg.pod_proj_list, SIGNAL("itemSelectionChanged()"), self.proj_list_change_cb)

	def proj_list_change_cb(self):
		item = self.dlg.pod_proj_list.selectedItems()[0]
		proj_dir = str(item.text())
		self.dlg.pod_proj_name.setText(str(proj_dir))
		self.path = proj_dir

	def open_btn_cb(self):
                fdlg = QFileDialog(None, "Choose project directory")
		fdlg.setFileMode(QFileDialog.Directory);
		fdlg.setDirectory(self.dlg.pod_proj_name.text())
		if (fdlg.exec_()):
			proj_dir = fdlg.selectedFiles()[0];
			self.dlg.pod_proj_name.setText(str(proj_dir))
                
	def ok_btn_cb(self):
		p = str(self.dlg.pod_proj_name.text()).strip()
		if (p == ''):
			self.dlg.setResult(2)
			return
		p = os.path.normpath(p)
		if (not os.path.isabs(p)):
			show_msg_dialog("\nProject path is not absolute")
			self.dlg.setResult(2)
			return
		if (not os.path.isdir(p)):
			show_msg_dialog("\nProject path is not a directory")
			self.dlg.setResult(2)
			return
		self.path = p

	def run_dialog(self, path_list):
		self.path = None
		self.dlg.pod_proj_name.setText('')
		self.dlg.pod_proj_list.addItems(path_list)
		while True:
			ret = self.dlg.exec_()
			if (ret == QDialog.Accepted or ret == QDialog.Rejected):
				break
		return self.path


def show_project_open_dialog(path_list):
	d = ProjectOpenDialog()
	return d.run_dialog(path_list)

class FilePreferencesDialog(QObject):
	def __init__(self, app_style, edit_ext_cmd):
		QObject.__init__(self)

		self.dlg = uic.loadUi('ui/preferences.ui')
		self.dlg.prd_style_lw.addItems(QStyleFactory.keys())
		self.dlg.prd_style_lw.itemSelectionChanged.connect(self.style_changed_cb)
		self.dlg.prd_font_app_btn.clicked.connect(self.font_app_btn_cb)
		self.set_btn_text_and_font(self.dlg.prd_font_app_btn, QApplication.font())
		self.app_style = app_style
		self.edit_ext_cmd = edit_ext_cmd
		if (self.edit_ext_cmd):
			self.dlg.prd_edit_ext_inp.setText(self.edit_ext_cmd)

	def set_btn_text_and_font(self, btn, font):
		ftext = font.family() + ' ' + str(font.pointSize())
		btn.setFont(font)
		btn.setText(ftext)

	def style_changed_cb(self):
		item = self.dlg.prd_style_lw.currentItem()
		self.app_style = item.text()
		QApplication.setStyle(self.app_style)

	def font_app_btn_cb(self):
		(font, ok) = QFontDialog().getFont(QApplication.font())
		if (ok):
			self.set_btn_text_and_font(self.dlg.prd_font_app_btn, font)
			
	def run_dialog(self):
		ret = self.dlg.exec_()
		if (ret == QDialog.Accepted):
			QApplication.setFont(self.dlg.prd_font_app_btn.font())
			self.edit_ext_cmd = self.dlg.prd_edit_ext_inp.text()
		return (self.app_style, self.dlg.prd_font_app_btn.font().toString(), self.edit_ext_cmd)

def show_preferences_dialog(app_style, edit_ext_cmd):
	d = FilePreferencesDialog(app_style, edit_ext_cmd)
	return d.run_dialog()

def show_about_dialog():
	d = uic.loadUi('ui/about.ui')
	p = QApplication.windowIcon().pixmap(128)
	d.ad_logo_lbl.setPixmap(p)
	d.exec_()

def show_goto_line_dialog(line, max_line):
	d = uic.loadUi('ui/goto_line.ui')
	d.gl_spinbox.setMaximum(max_line)
	d.gl_hslider.setMaximum(max_line)
	d.gl_spinbox.setValue(line)
	d.gl_spinbox.lineEdit().selectAll()
	if (d.exec_() == QDialog.Accepted):
		return d.gl_spinbox.value()
	return None

class FindDialog:
	dlg = None
	def __init__(self):
		self.dlg = uic.loadUi('ui/find.ui')
		self.dlg.ft_text_inp.setAutoCompletion(False)
		self.dlg.ft_text_inp.setInsertPolicy(QComboBox.InsertAtTop)

	def run_dlg(self, text):
		if (text == None):
			text = ''
		d = self.dlg
		d.ft_text_inp.lineEdit().setText(text)
		d.ft_text_inp.lineEdit().selectAll()
		d.ft_text_inp.lineEdit().setFocus()
		d.ft_from_cursor.setChecked(True)
		while True:
			ret = d.exec_()
			if (ret != QDialog.Accepted):
				return None
			text = d.ft_text_inp.currentText()
			text = str(text).strip()
			if (text != ''):
				break
		opt = {
			'cs' : d.ft_cs.isChecked(),
			're' : d.ft_re.isChecked(),
			'wo' : d.ft_wo.isChecked(),
			'fw' : not d.ft_bw.isChecked(),
			'cursor' : d.ft_from_cursor.isChecked(),
		}
		return (text, opt)

def show_find_dialog(text):
	if (FindDialog.dlg == None):
		FindDialog.dlg = FindDialog()
	return FindDialog.dlg.run_dlg(text)


class QueryDialog:
	dlg = None
	def __init__(self):
		self.dlg = uic.loadUi('ui/cs_opt.ui')
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
		self.dlg.qd_sym_inp.setAutoCompletion(False)
		self.dlg.qd_sym_inp.setInsertPolicy(QComboBox.InsertAtTop)
		self.dlg.qd_cmd_inp.addItems(self.cmd_items)

	def run_dialog(self, cmd_id, req):
		if (cmd_id > 5):
			cmd_id = cmd_id - 1
		self.dlg.qd_cmd_inp.setCurrentIndex(cmd_id)
		if (req == None):
			req = ''
		self.dlg.qd_sym_inp.setFocus()
		self.dlg.qd_sym_inp.setEditText(req)
		self.dlg.qd_sym_inp.lineEdit().selectAll()
		self.dlg.qd_substr_chkbox.setChecked(False)
		self.dlg.qd_icase_chkbox.setChecked(False)

		if (self.dlg.exec_() == QDialog.Accepted):
			cmd_id = self.dlg.qd_cmd_inp.currentIndex()
			if (cmd_id > 5):
				cmd_id = cmd_id + 1
			req = str(self.dlg.qd_sym_inp.currentText())
			#self.dlg.qd_sym_inp.addItem(req)
			if (req != '' and self.dlg.qd_substr_chkbox.isChecked()):
				req = '.*' + req + '.*'
			opt = None
			if (self.dlg.qd_icase_chkbox.isChecked()):
				opt = '-C'
			res = (cmd_id, req, opt)
			return res
		return None
		
def show_query_dialog(cmd_id, req):
	if (QueryDialog.dlg == None):
		QueryDialog.dlg = QueryDialog()
	return QueryDialog.dlg.run_dialog(cmd_id, req)

class FilterDialog:
	def __init__(self):
		self.dlg = uic.loadUi('ui/filter.ui')
		self.cmd_items = [
			'Function',
			'File',
			'Line',
			'Text'
		]
		self.dlg.fd_cmd_inp.addItems(self.cmd_items)

	def run_dialog(self):
		res = None
		if self.dlg.exec_() == QDialog.Accepted:
			res = [
				str(self.dlg.fd_filter_inp.text()),
				self.dlg.fd_regex_chkbox.isChecked(),
				self.dlg.fd_negate_chkbox.isChecked(),
				self.dlg.fd_icase_chkbox.isChecked()
			]
		self.dlg = None
		return res

def show_filter_dialog():
	dlg = FilterDialog()
	return dlg.run_dialog()
