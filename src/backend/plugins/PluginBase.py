from PyQt4.QtCore import *

class ProjectBase(QObject):
	prj = None
	qry = None

	def __init__(self):
		QObject.__init__(self)

	def prj_close(self):
		print 'ProjectBase: Not implemeted'

	def prj_get_dir(self):
		print 'ProjectBase: Not implemeted'
	def prj_get_name(self):
		print 'ProjectBase: Not implemeted'
	def prj_get_src_files(self):
		print 'ProjectBase: Not implemeted'

	def prj_is_open(self):
		print 'ProjectBase: Not implemeted'
	def prj_is_ready(self):
		print 'ProjectBase: Not implemeted'
	def prj_get_conf(self):
		print 'ProjectBase: Not implemeted'
	def prj_update_conf(self, proj_args):
		print 'ProjectBase: Not implemeted'

	def prj_show_settings(self, proj_args):
		print 'ProjectBase: Not implemeted'
	def prj_settings(self, proj_args):
		print 'ProjectBase: Not implemeted'

class ConfigBase(QObject):
	@staticmethod
	def prepare_menu(menubar):
		pass

class QueryBase(QObject):
	@staticmethod
	def prepare_menu(menubar):
		pass

class QueryUiBase(QObject):
	backend_menu = None
	edit_book = None
	res_book = None
	call_view = None
	dbg_mgr = None

	def __init__(self):
		QObject.__init__(self)
		self.prepare_menu()

	def prepare_menu(self):
		print 'Plugin is not implementing prepare_menu'

