from PyQt4.QtCore import *

def msg_box(msg):
	QMessageBox.warning(None, "Seascope", msg, QMessageBox.Ok)

class ProjectBase(QObject):
	prj = None
	qry = None

	def __init__(self):
		QObject.__init__(self)

	def prj_close(self):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))

	def prj_get_dir(self):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))
	def prj_get_name(self):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))
	def prj_get_src_files(self):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))

	def prj_is_open(self):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))
	def prj_is_ready(self):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))
	def prj_get_conf(self):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))
	def prj_update_conf(self, proj_args):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))

	def prj_show_settings(self, proj_args):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))
	def prj_settings(self, proj_args):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))

class ConfigBase(QObject):
	@staticmethod
	def prepare_menu(menubar):
		pass

class QueryBase(QObject):
	@staticmethod
	def prepare_menu(menubar):
		pass

	def query(self, cmd_str, req, opt):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))
		
	def rebuild():
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))
		

import PluginHelper

class QueryUiBase(QObject):
	def __init__(self):
		QObject.__init__(self)
		self.prepare_menu()

	def prepare_menu(self):
		msg_box('%s: %s: Not implemeted' % (__name__, __func__))

	def query_ctree(self, req, opt):
		PluginHelper.call_view_page_new(req, self.query.query, self.ctree_args, opt)

	def query_qdef(self, req, opt):
		sig_res = self.query.query('DEF', req, opt)
		PluginHelper.quick_def_page_new(sig_res)

	def do_query(self, cmd_str, req, opt):
		## create page
		name = cmd_str + ' ' + req
		sig_res = self.query.query(cmd_str, req, opt)
		PluginHelper.result_page_new(name, sig_res)




from PyQt4.QtGui import QMessageBox

class QuerySignal(QObject):
	sig_result = pyqtSignal(str, list)
	sig_result_dbg = pyqtSignal(str, str, str)
	sig_rebuild = pyqtSignal()

	def __init__(self):
		QObject.__init__(self)

class PluginProcess(QObject):
	proc_list = []

	def __init__(self, wdir):
		QObject.__init__(self)
		
		PluginProcess.proc_list.append(self)
		self.is_rebuild = False

		self.sig = QuerySignal()

		self.proc = QProcess()
		self.proc.finished.connect(self._finished_cb)
		self.proc.error.connect(self._error_cb)

		self.proc.setWorkingDirectory(wdir)
		self.wdir = wdir

	def _cleanup(self):
		PluginProcess.proc_list.remove(self)
		if self.err_str != '':
			QMessageBox.warning(None, "Seascope", str(self.err_str), QMessageBox.Ok)

	def _error_cb(self, err):
		err_dict = { 
			QProcess.FailedToStart:	'FailedToStart',
			QProcess.Crashed:	'Crashed',
			QProcess.Timedout:	'The last waitFor...() function timed out',
			QProcess.WriteError:	'An error occurred when attempting to write to the process',
			QProcess.ReadError:	'An error occurred when attempting to read from the process',
			QProcess.UnknownError:	'An unknown error occurred',
		}
		self.err_str = '<b>' + self.p_cmd + '</b><p>' + err_dict[err]
		self._cleanup()

	def _finished_cb(self, ret):
		res = str(self.proc.readAllStandardOutput())
		self.err_str = str(self.proc.readAllStandardError())
		
		#print 'output', res
		print 'cmd:', self.p_cmd
		if self.is_rebuild:
			self.sig.sig_rebuild.emit()
		else:
			self.sig.sig_result_dbg.emit(self.p_cmd, res, self.err_str)
			res = self.parse_result(res, self.sig)
			if res != None:
				self.sig.sig_result.emit(self.sig.sym, res)

		self._cleanup()

	def run_query_process(self, pargs, sym):
		self.sig.sym = sym
		self.p_cmd = ' '.join(pargs)
		print 'pp:cmd:', pargs[0], pargs[1:]
		self.proc.start(pargs[0], pargs[1:])
		if self.proc.waitForStarted() == False:
			return None
		self.proc.closeWriteChannel()
		return [self.sig.sig_result, self.sig.sig_result_dbg]

	def run_rebuild_process(self, pargs):
		self.is_rebuild = True
		self.p_cmd = ' '.join(pargs)
		self.proc.start(pargs[0], pargs[1:])
		if self.proc.waitForStarted() == False:
			return None
		print 'cmd:', pargs
		return self.sig.sig_rebuild

	def parse_result(self, text, sig):
		print 'parse_result not implemented'
		if text == '':
			text = ['Empty output']
		else:
			text = text.strip().split('\n')
		return text

	def apply_ctags_fix(self, res, cond_list):
		CtagsCache.apply_ctags_fix(res, cond_list)

if __name__ == '__main__':
	import sys

	def slot_result(sym, res):
		print 'slot_result:    ', [str(sym), res]
		sys.exit(0)
	def slot_result_dbg(cmd, res, err_str):
		print 'slot_result_dbg:', [str(cmd), str(res).strip().split('\n'), str(err_str)]
	def slot_rebuild():
		print 'slot_rebuild'

	app = QCoreApplication(sys.argv)

	#qsig = PluginProcess('.').run_query_process(['ls'], 'ls')
	qsig = PluginProcess('/home/anil/prj/ss/lin').run_query_process(['cscope', '-q', '-k', '-L', '-d', '-0', 'vdso'], 'ls')
	if qsig == None:
		sys.exit(-1)
	qsig[0].connect(slot_result)
	qsig[1].connect(slot_result_dbg)

	app.exec_()
