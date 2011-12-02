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
	def __init__(self):
		QObject.__init__(self)
		self.prepare_menu()

	def prepare_menu(self):
		print 'Plugin is not implementing prepare_menu'


from PyQt4.QtGui import QMessageBox

class PluginProcess(QObject):
	sig_result = pyqtSignal(str, list)
	sig_result_dbg = pyqtSignal(str, str, str)
	sig_rebuild = pyqtSignal()

	proc_list = []

	def __init__(self, wdir):
		QObject.__init__(self)
		
		self.is_rebuild = False
		PluginProcess.proc_list.append(self)

		self.proc = QProcess()
		self.proc.finished.connect(self._finished_cb)

		self.proc.setWorkingDirectory(wdir)
		self.wdir = wdir

	def _finished_cb(self, ret):
		PluginProcess.proc_list.remove(self)
		
		res = str(self.proc.readAllStandardOutput())
		err_str = str(self.proc.readAllStandardError())

		print 'output', res
		print 'cmd:', self.p_cmd
		if self.is_rebuild:
			self.sig_rebuild.emit()
		else:
			self.sig_result_dbg.emit(self.p_cmd, res, err_str)
			res = self.parse_result(res)
			self.sig_result.emit(self.p_sym, res)

		if (err_str != ''):
			QMessageBox.warning(None, "SeaScope", str(err_str), QMessageBox.Ok)

	def run_query_process(self, pargs, sym):
		self.p_sym = sym
		self.p_cmd = pargs
		self.proc.start(pargs)
		self.proc.closeWriteChannel()
		return [self.sig_result, self.sig_result_dbg]

	def run_rebuild_process(self, pargs):
		self.is_rebuild = True
		self.p_cmd = pargs
		self.proc.start(pargs)
		return self.sig_rebuild

	def parse_result(self, text):
		print 'parse_result not implemented'

	def _ctags_for_file(self, filename):
		cmd = 'ctags -n -u --fields=+K -f -'
		args = cmd.split()
		args.append(filename)
		import subprocess
		proc = subprocess.Popen(args, stdout=subprocess.PIPE)
		(out_data, err_data) = proc.communicate()
		out_data = out_data.split('\n')
		res = []
		for line in out_data:
			if (line == ''):
				break
			line = line.split('\t')
			num = line[2].split(';', 1)[0]
			line = [line[0], num, line[3]]
			res.append(line)
		return res

	def _ctags_fix(self, line):
		f = line[1]
		n = int(line[2])
		if f not in self.ct_dict:
			#print 'ctags_for_file: ', f
			self.ct_dict[f] = self._ctags_for_file(f)
		prev = None
		for k in self.ct_dict[f]:
			#print k
			if int(k[1]) > n:
				break
			prev = k
		if prev:
			line[0] = '[' + prev[0] + ']'

	def apply_ctags_fix(self, res, cond_list):
		import os
		if not os.path.exists(os.path.expanduser('~/.seascope_ctags_fix')):
			return
		self.ct_dict = {}
		for line in res:
			if line[0] in cond_list:
				self._ctags_fix(line)
		self.ct_dict = {}
