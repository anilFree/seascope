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

		#print 'output', res
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

	def apply_ctags_fix(self, res, cond_list):
		CtagsCache.apply_ctags_fix(res, cond_list)


class CtagsCache:
	ctc = None

	@staticmethod
	def apply_ctags_fix(res, cond_list):
		import os
		if os.path.exists(os.path.expanduser('~/.seascope_no_ctags_fix')):
			return

		if CtagsCache.ctc == None:
			CtagsCache.ctc = CtagsCache()

		from datetime import datetime
		
		t1 = datetime.now()
		flist = set()
		for line in res:
			if line[1] not in CtagsCache.ctc.ct_dict:
				flist.add(line[1])

		t2 = datetime.now()
		print '  ', len(flist), 'flist', t2 - t1

		#for f in flist:
			#if f not in CtagsCache.ctc.ct_dict:
				#CtagsCache.ctc.ct_dict[f] = CtagsCache.ctc._ctags_for_file(f)
		CtagsCache.ctc._ctags_for_file_list(flist)
		
		t3 = datetime.now()
		print '  ct', t3 - t2

		for line in res:
			if line[0] in cond_list:
				CtagsCache.ctc._ctags_fix(line)

		t4 = datetime.now()
		print '  fix', t4 - t3
		print '  total', t4 - t1

	@staticmethod
	def flush():
		CtagsCache.ctc = None

	def __init__(self):
		self.ct_dict = {}

	def _ctags_fix(self, line):
		f = line[1]
		n = int(line[2])

		ct = self.ct_dict[f]
		x = -1
		y = len(ct) - 1

		#print f, n
		while x < y:
			m = (x + y + 1) / 2
			#print '(', x, y, m, ')'
			if ct[m][1] > n:
				#print 'y: m -1', ct[m][1]
				m = m - 1
				y = m
				continue
			if ct[m][1] < n:
				#print 'x: m', ct[m][1]
				x = m
				continue
			break
		if y == -1:
			return
		#assert x == m or y == m or ct[m][1] == n
		line[0] = ct[m][0]

	def _ctags_fix_linear(self, line):
		f = line[1]
		n = int(line[2])
		if f not in self.ct_dict:
			#print 'ctags_for_file: ', f
			self.ct_dict[f] = self._ctags_for_file(f)
		prev = None
		for k in self.ct_dict[f]:
			#print k
			kn = int(k[1])
			if kn > n:
				break
			#if kn == n:
			prev = k
			#break
		if prev:
			line[0] = prev[0]
			#line[2] = '0000' + line[2]

	def _ctags_for_file(self, filename):
		#print 'ct:', filename
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

	def _ctags_for_file_list(self, flist):
		cmd = 'ctags -n -u --fields=+K -L - -f -'
		args = cmd.split()
		import subprocess
		proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		(out_data, err_data) = proc.communicate('\n'.join(flist))
		out_data = out_data.split('\n')
		res = []
		for f in flist:
			self.ct_dict[f] = []
		for line in out_data:
			if (line == ''):
				break
			line = line.split('\t')
			f = line[1]
			num = line[2].split(';', 1)[0]
			line = [line[0], int(num), line[3]]
			self.ct_dict[f].append(line)
		return res


