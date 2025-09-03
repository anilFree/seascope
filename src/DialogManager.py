#!/usr/bin/env python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import sys
import os
import string

from PyQt6 import QtWidgets, QtGui, QtCore, uic

from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *


def show_msg_dialog(msg):
	QMessageBox.information(None, "Seascope", msg, QMessageBox.StandardButton.Ok)

def show_yes_no(msg):
	ret = QMessageBox.question(None, "Seascope", msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
	return ret == QMessageBox.StandardButton.Yes

def show_yes_no_dontask(msg):
	mb = QMessageBox(None)
	mb.setIcon(QMessageBox.Icon.Question)
	mb.setWindowTitle("Seascope")
	mb.setText(msg)
	mb.addButton('Yes', QMessageBox.ButtonRole.YesRole)
	mb.addButton('No', QMessageBox.ButtonRole.NoRole)
	mb.addButton("Yes, Don't ask again", QMessageBox.ButtonRole.YesRole)
	return mb.exec()

def show_proj_close():
	return show_yes_no("\nClose current project?")

class ProjectOpenDialog(QObject):
	def __init__(self):
		QObject.__init__(self)

		self.dlg = uic.loadUi('ui/proj_open.ui')
		self.dlg.pod_open_btn.setIcon(QFileIconProvider().icon(QFileIconProvider.IconType.Folder))

		self.dlg.pod_open_btn.clicked.connect(self.open_btn_cb)
		self.dlg.accepted.connect(self.ok_btn_cb)
		self.dlg.pod_proj_list.itemSelectionChanged.connect(self.proj_list_change_cb)

	def proj_list_change_cb(self):
		item = self.dlg.pod_proj_list.selectedItems()[0]
		proj_dir = str(item.text())
		self.dlg.pod_proj_name.setText(str(proj_dir))
		self.path = proj_dir

	def open_btn_cb(self):
		fdlg = QFileDialog(None, "Choose project directory")
		fdlg.setFileMode(QFileDialog.Directory);
		fdlg.setDirectory(self.dlg.pod_proj_name.text())
		if (fdlg.exec()):
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
			ret = self.dlg.exec()
			if (ret == QDialog.DialogCode.Accepted or ret == QDialog.DialogCode.Rejected):
				break
		return self.path


def show_project_open_dialog(path_list):
	d = ProjectOpenDialog()
	return d.run_dialog(path_list)

class FilePreferencesDialog(QObject):
	def __init__(self, app_style, edit_ext_cmd, ev_font, dontask, innered, ln_nr):
		QObject.__init__(self)

		self.dlg = uic.loadUi('ui/preferences.ui')
		self.dlg.prd_style_lw.addItems(list(QStyleFactory.keys()))
		self.dlg.prd_style_lw.itemSelectionChanged.connect(self.style_changed_cb)
		self.dlg.prd_font_app_btn.clicked.connect(self.font_app_btn_cb)
		self.dlg.prd_font_ev_btn.clicked.connect(self.font_ev_btn_cb)
		self.set_btn_text_and_font(self.dlg.prd_font_app_btn, QApplication.font())
		self.set_btn_text_and_font(self.dlg.prd_font_ev_btn, ev_font)
		self.app_style = app_style
		self.ev_font = ev_font
		self.edit_ext_cmd = edit_ext_cmd
		self.exit_dontask = dontask
		self.inner_editing = innered
		self.show_ln_nr = ln_nr
		if self.exit_dontask:
			self.dlg.prd_opt_ask_chkb.setCheckState(Qt.CheckState.Unchecked)
		else:
			self.dlg.prd_opt_ask_chkb.setCheckState(Qt.CheckState.Checked)
		if self.inner_editing:
			self.dlg.prd_opt_inner_ed.setCheckState(Qt.CheckState.Checked)
		else:
			self.dlg.prd_opt_inner_ed.setCheckState(Qt.CheckState.Unchecked)
		if self.show_ln_nr:
			self.dlg.prd_opt_show_ln_nr.setCheckState(Qt.CheckState.Checked)
		else:
			self.dlg.prd_opt_show_ln_nr.setCheckState(Qt.CheckState.Unchecked)
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

	def font_ev_btn_cb(self):
		(font, ok) = QFontDialog().getFont(self.ev_font)
		if (ok):
			self.set_btn_text_and_font(self.dlg.prd_font_ev_btn, font)
			
	def run_dialog(self):
		ret = self.dlg.exec()
		if (ret == QDialog.DialogCode.Accepted):
			QApplication.setFont(self.dlg.prd_font_app_btn.font())
			self.ev_font = self.dlg.prd_font_ev_btn.font()
			self.edit_ext_cmd = self.dlg.prd_edit_ext_inp.text()
			self.exit_dontask = self.dlg.prd_opt_ask_chkb.checkState() == Qt.CheckState.Unchecked
			self.inner_editing = self.dlg.prd_opt_inner_ed.checkState() == Qt.CheckState.Checked
			self.show_ln_nr = self.dlg.prd_opt_show_ln_nr.checkState() == Qt.CheckState.Checked
		return (self.app_style, self.dlg.prd_font_app_btn.font().toString(), self.edit_ext_cmd, 
			self.ev_font.toString(), self.exit_dontask, self.inner_editing, self.show_ln_nr)

def show_preferences_dialog(app_style, edit_ext_cmd, ev_font, dontask, innered, ln_nr):
	d = FilePreferencesDialog(app_style, edit_ext_cmd, ev_font, dontask, innered, ln_nr)
	return d.run_dialog()

def show_about_dialog():
	d = uic.loadUi('ui/about.ui')
	p = QApplication.windowIcon().pixmap(128)
	d.ad_logo_lbl.setPixmap(p)
	d.exec()

def show_goto_line_dialog(line, max_line):
	d = uic.loadUi('ui/goto_line.ui')
	d.gl_spinbox.setMaximum(max_line)
	d.gl_hslider.setMaximum(max_line)
	d.gl_spinbox.setValue(line)
	d.gl_spinbox.lineEdit().selectAll()
	d.gl_spinbox.lineEdit().setFocus()
	if (d.exec() == QDialog.DialogCode.Accepted):
		return d.gl_spinbox.value()
	return None

class FindDialog:
	dlg = None
	def __init__(self):
		self.dlg = uic.loadUi('ui/find.ui')
		self.dlg.ft_text_inp.setCompleter(None)
		self.dlg.ft_text_inp.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)
		self.dlg.ft_text_inp.setFocus()

	def run_dlg(self, text):
		if (text == None):
			text = ''
		d = self.dlg
		d.ft_text_inp.lineEdit().setText(text)
		d.ft_text_inp.lineEdit().selectAll()
		d.ft_text_inp.lineEdit().setFocus()
		d.ft_from_cursor.setChecked(True)
		while True:
			ret = d.exec()
			if (ret != QDialog.DialogCode.Accepted):
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

class FilterDialog:
	def __init__(self, cmd_items, cmd_sel):
		self.dlg = uic.loadUi('ui/filter.ui')
		self.dlg.fd_cmd_inp.addItems(cmd_items)
		self.dlg.fd_cmd_inp.setCurrentIndex(cmd_items.index(cmd_sel))
		self.dlg.fd_filter_inp.setFocus()
		self.dlg.fd_regex_err_lbl.setVisible(False)

	def run_dialog(self):
		while True:
			ret = self.dlg.exec()
			if ret != QDialog.DialogCode.Accepted:
				return None
			is_regex = self.dlg.fd_regex_chkbox.isChecked()
			text = str(self.dlg.fd_filter_inp.text())
			if is_regex == True:
				try:
					import re
					re.compile(text)
				except:
					e = str(sys.exc_info()[1])
					lbl = self.dlg.fd_regex_err_lbl
					lbl.setVisible(True)
					lbl.setText("<font color='red'>regex: " + e + '</font>')
					continue
					
			res = [
				text,
				is_regex,
				self.dlg.fd_negate_chkbox.isChecked(),
				self.dlg.fd_icase_chkbox.isChecked(),
				str(self.dlg.fd_cmd_inp.currentText())
			]
			return res

def show_filter_dialog(cmd_items, cmd_sel):
	dlg = FilterDialog(cmd_items,cmd_sel)
	return dlg.run_dialog()
