# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

from PyQt4.QtCore import *
from PyQt4.QtGui import *

backend_menu = None
edit_book = None
res_book = None
call_view = None
class_graph_view = None
file_view = None
dbg_view = None

def editor_current_file():
	(f, l) = edit_book.get_current_file_line()
	return f

def editor_current_word():
	return edit_book.get_current_word()

def result_page_new(name, sig_res):
	if sig_res == None:
		return
	page = res_book.create_result_page(name)
	## add result
	sig_res[0].connect(page.add_result)
	#page.add_result(req, res)
	dbg_view.connect_to_sig(sig_res[1])

def _quick_def_result(req, res):
	count = len(res)
	if count > 1:
		page = res_book.create_result_page_single()
		page.add_result(req, res)
		
		dlg = QDialog()
		dlg.setWindowTitle('Quick Definition: ' + req)
		vlay = QVBoxLayout(dlg)
		vlay.addWidget(page)

		page.sig_show_file_line.connect(edit_book.show_file_line)
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
		edit_book.show_file_line(filename, line)

def quick_def_page_new(sig_res):
	if sig_res == None:
		return
	sig_res[0].connect(_quick_def_result)
	dbg_view.connect_to_sig(sig_res[1])

def call_view_page_new(req, query_func, ctree_query_args, opt):
	hint_file = editor_current_file()
	call_view.create_page(req, query_func, ctree_query_args, opt, hint_file)

def class_graph_view_page_new(req, dname, proj_dir, query_func, clgraph_query_args, opt):
	class_graph_view.create_page(req, dname, proj_dir, query_func, clgraph_query_args, opt)

def file_view_update(flist):
	file_view.add_files(flist)
