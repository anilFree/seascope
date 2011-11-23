import subprocess

from PyQt4.QtCore import *
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
		self.proc.finished.connect(self.pp_finished)

		self.proc.setWorkingDirectory(wdir)

	def pp_finished(self, ret):
		PluginProcess.proc_list.remove(self)
		
		res = str(self.proc.readAllStandardOutput())
		err_str = str(self.proc.readAllStandardError())

		print 'output', res
		if self.is_rebuild:
			self.sig_rebuild.emit()
		else:
			self.sig_result_dbg.emit(self.s_args, res, err_str)
			res = self.gt_parse_result(res)
			self.sig_result.emit(self.sym, res)

		if (err_str != ''):
			QMessageBox.warning(None, "SeaScope", str(err_str), QMessageBox.Ok)


class GtProcess(PluginProcess):

	def gt_parse_result(self, text):
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

	def gt_query_int(self, cmd_id, sym, opt):
		if (opt == None):
			opt = ''
		self.sym = sym
		self.s_args = 'global ' + self.args + opt + ' -a --result=cscope ' +' -x ' + str(cmd_id) + ' ' + sym
		self.proc.start(self.s_args)
		self.proc.closeWriteChannel()
		return [self.sig_result, self.sig_result_dbg]

	def gt_rebuild_int(self):
		self.is_rebuild = True
		self.s_args = 'gtags ' + ' -i'
		self.proc.start(self.s_args)
		return self.sig_rebuild

	@staticmethod
	def gt_query(wdir, cmd_id, sym, opt):
		p = GtProcess()
		res = p.gt_query_int(cmd_id, sym, opt)
		return res

	@staticmethod
	def gt_rebuild():
		p = GtProcess()
		res = p.gt_rebuild_int()
		return res
