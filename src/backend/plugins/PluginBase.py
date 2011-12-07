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
			QMessageBox.warning(None, "SeaScope", str(self.err_str), QMessageBox.Ok)

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
			res = self.parse_result(res)
			self.sig.sig_result.emit(self.p_sym, res)

		self._cleanup()

	def run_query_process(self, pargs, sym):
		self.p_sym = sym
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

	def parse_result(self, text):
		print 'parse_result not implemented'
		if text == '':
			text = ['Empty output']
		else:
			text = text.strip().split('\n')
		return text

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
