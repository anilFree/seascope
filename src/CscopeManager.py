import subprocess

from PyQt4.QtCore import *
from PyQt4.QtGui import QMessageBox

class CsProcess(QObject):
	sig_result = pyqtSignal(str, list)
	sig_rebuild = pyqtSignal()

	cs_wdir = None
	cs_args = None
	cs_plist = []

	def __init__(self):
		QObject.__init__(self)
		
		self.is_rebuild = False
		CsProcess.cs_plist.append(self)

		self.args = CsProcess.cs_args
		self.proc = QProcess()
		self.proc.setWorkingDirectory(CsProcess.cs_wdir)
		self.proc.finished.connect(self.cs_finished)
	
	def cs_finished(self, ret):
		CsProcess.cs_plist.remove(self)
		res = str(self.proc.readAllStandardOutput())
		if self.is_rebuild:
			self.sig_rebuild.emit()
		else:
			res = self.cs_parse_result(res)
			self.sig_result.emit(self.sym, res)

		err_str = str(self.proc.readAllStandardError())
		if (err_str != ''):
			QMessageBox.warning(None, "SeaScope", str(err_str), QMessageBox.Ok)


	def cs_parse_result(self, text):
		text = text.split('\n')
		res = []
		for line in text:
			if line == '':
				continue
			if line[-1:] == '\r':
				line = line[0:-1]
			line = line.split(' ', 3)
			line = [line[1], line[0], line[2], line[3]]
			res.append(line)
		#if len(res) > 0:
			#print res[0], '...', len(res), 'results'
		#else:
			#print '0 results'
		return res

	def cs_query_int(self, cmd_id, sym, opt):
		if (opt == None):
			opt = ''
		self.sym = sym
		args = 'cscope ' + self.args + ' -L -d ' + opt + ' -' + str(cmd_id) + ' ' + sym
		#print 'args:', args
		self.proc.start(args)
		self.proc.closeWriteChannel()
		return self.sig_result

	def cs_rebuild_int(self):
		self.is_rebuild = True
		args = 'cscope ' + self.args + ' -L'
		#print 'args:', args
		self.proc.start(args)
		return self.sig_rebuild

	@staticmethod
	def cs_setup(args, wdir):
		CsProcess.cs_args = args
		CsProcess.cs_wdir = wdir
	
	@staticmethod
	def cs_setup_clear():
		CsProcess.cs_setup(None, None)
	
	@staticmethod
	def cs_query(cmd_id, sym, opt):
		p = CsProcess()
		res = p.cs_query_int(cmd_id, sym, opt)
		return res
	@staticmethod
	def cs_rebuild():
		p = CsProcess()
		res = p.cs_rebuild_int()
		return res
