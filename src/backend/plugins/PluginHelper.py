from PyQt4.QtCore import *
from PyQt4.QtGui import *

backend_menu = None
edit_book = None
res_book = None
call_view = None
file_view = None
dbg_mgr = None

def editor_current_word():
	return edit_book.get_current_word()

def result_page_new(name, sig_res):
	page = res_book.create_result_page(name)
	## add result
	sig_res[0].connect(page.add_result)
	#page.add_result(req, res)
	dbg_mgr.connect_to_cs_sig_res(sig_res[1])

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
	sig_res[0].connect(_quick_def_result)
	dbg_mgr.connect_to_cs_sig_res(sig_res[1])

def call_view_page_new(req, query_func, ctree_query_args, opt):
	call_view.create_page(req, query_func, ctree_query_args, opt)

def file_view_update(src_list):
	self.file_view.add_files(src_files)
