# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os, re
import copy

from PyQt4.QtCore import QObject, pyqtSignal, QProcess

def NOT_IMPLEMENTED(n, f):
	msg = '%s: %s: Not implemeted' % (n, f)
	from PyQt4.QtGui import QMessageBox
	QMessageBox.warning(None, "Seascope", msg, QMessageBox.Ok)

import CtagsCache

cmd_table_master = [
	[	'REF',		['&References',		'Ctrl+0'],	['References to'	]	],
	[	'DEF',		['&Definitions',	'Ctrl+1'],	['Definition of'	]	],
	[	'<--',		['&Called Functions',	'Ctrl+2'],	['Functions called by'	]	],
	[	'-->',		['C&alling Functions',	'Ctrl+3'],	['Functions calling'	]	],
	[	'TXT',		['Find &Text',		'Ctrl+4'],	['Find text'		]	],
	[	'GREP',		['Find &Egrep',		'Ctrl+5'],	['Find egrep pattern'	]	],
	[	'FIL',		['Find &File',		'Ctrl+7'],	['Find files'		]	],
	[	'INC',		['&Include/Import',	'Ctrl+8'],	['Find include/import'	]	],
	[	'---',		[None,				],	None				],
	[	'QDEF', 	['&Quick Definition',	'Ctrl+]'],	None				],
	[	'CTREE',	['Call Tr&ee',		'Ctrl+\\'],	['Call tree'		]	],
	[	'---',		[None,				],	None				],
	[	'CLGRAPH',  	['Class &Graph',	'Ctrl+:'],	['Class graph'		]	],
	[	'CLGRAPHD', 	['Class Graph Dir',	'Ctrl+;'],	['Class graph dir'	]	],
	[	'FFGRAPH', 	['File Func Graph',	'Ctrl+^'],	['File Func graph dir'	]	],
	[	'---',		[None,				],	None				],
	[	'UPD',		['Re&build Database',	None	],	None				],
]
class PluginFeatureBase:
	def __init__(self):
		self.clgraph_query_args = [
			['CLGRAPH',	'D', 'Derived classes'			],
			['CLGRAPH',	'B', 'Base classes'			],
		]
		self.clgraph_query_args = [
			['CLGRAPH',	'D', 'Derived classes'			],
			['CLGRAPH',	'B', 'Base classes'			],
		]
		self.ffgraph_query_args = [
			['FFGRAPH',    'F',   'File functions graph'],
			['FFGRAPH_E',  'F+E', 'File functions + external graph'],
			['FFGRAPH_D',  'D',   'Directory functions graph'],
			['FFGRAPH_DE', 'D+E', 'Directory functions + external graph']
		]
	
	def setup(self):
		feat_cmds = [ d[0] for d in self.feat_desc ]
		ct = copy.deepcopy(cmd_table_master)
		self.cmd_table = [ t for t in ct if t[0] in feat_cmds or t[0] == '---' ]

		self.menu_cmd_list = [ [c[0]] + c[1] for c in self.cmd_table ]

		self.cmd_str2id = {}
		self.cmd_str2qstr = {}
		self.cmd_qstr2str = {}
		for c in self.feat_desc:
			self.cmd_str2id[c[0]] = c[1]
		for c in self.cmd_table:
			if c[2] != None:
				self.cmd_str2qstr[c[0]] = c[2][0]
				self.cmd_qstr2str[c[2][0]] = c[0]
		# python 2.7
		#self.cmd_str2id = { c[0]:c[1] for c in self.feat_desc }
		#self.cmd_str2qstr = { c[0]:c[2][0] for c in self.cmd_table if c[1] }
		#self.cmd_qstr2str = { c[2][0]:c[0] for c in self.cmd_table if c[1] }
		self.cmd_qstrlist = [ c[2][0] for c in self.cmd_table if c[2] ]

class ProjectBase(QObject):
	prj = None
	qry = None

	def __init__(self):
		QObject.__init__(self)
		self.feat = None

	def prj_close(self):
		if (self.conf != None):
			self.conf.proj_close()
		self.conf = None

	def prj_dir(self):
		return self.conf.c_dir
	def prj_name(self):
		return self.conf.get_proj_name()
	def prj_src_files(self):
		return self.conf.get_proj_src_files()

	def prj_is_open(self):
		return self.conf != None
	def prj_is_ready(self):
		return self.conf.is_ready()

	def prj_conf(self):
		return self.conf.get_proj_conf()
		
	def prj_update_conf(self, proj_args):
		self.conf.proj_update(proj_args)

	def prj_show_settings(self, proj_args):
		NOT_IMPLEMENTED(__name__, __func__)
	def prj_settings(self, proj_args):
		NOT_IMPLEMENTED(__name__, __func__)

	def prj_feature_setup(self):
		self.feat.setup()

	def prj_query(self, rquery):
		return self.qry.query(rquery)

	def prj_rebuild(self):
		return self.qry.rebuild()

	def prj_query_fl(self):
		return self.qry.query_fl()

	def prj_type(self):
		return self.conf.prj_type

	def prj_feature(self):
		return self.feat

	def prj_settings_get(self):
		proj_args = self.prj_conf()
		return proj_args

	def prj_settings_update(self, proj_args):
		NOT_IMPLEMENTED(__name__, __func__)
		return

class ConfigBase(QObject):
	def __init__(self, ptype):
		self.prj_type = ptype
		self.c_dir = ''
		self.c_opt = ''
		self.c_flist = []

	def get_proj_name(self):
		return os.path.split(self.c_dir)[1]

	def get_proj_src_files(self):
		fl = self.c_flist
		return fl

	def get_proj_conf(self):
		return (self.c_dir, self.c_opt, self.c_flist)

	def read_config(self):
		pass
	def write_config(self):
		pass

	def proj_start(self):
		pass

	def proj_open(self, proj_path):
		self.c_dir = proj_path
		self.read_config()
		self.proj_start()

	def proj_update(self, proj_args):
		self.proj_new(proj_args)
		
	def proj_new(self, proj_args):
		self.proj_args = proj_args
		(self.c_dir, self.c_opt, self.c_flist) = proj_args
		self.write_config()
		self.proj_start()

	def proj_close(self):
		pass

	def is_ready(self):
		return True

	@staticmethod
	def prepare_menu(menubar):
		pass

class QueryBase(QObject):
	@staticmethod
	def prepare_menu(menubar):
		pass

	def query(self, rquery):
		cmd_str = rquery['cmd']
		req     = rquery['req']
		opt     = rquery['opt']
		if opt == None:
			opt = []

		pargs = []
		if cmd_str == 'GREP':
			pargs = ['grep', '-E', '-R', '-n', '-I']
			pargs += [ '--', req ]
			pargs += [self.conf.c_dir]
		else:
			assert(false)
			return None
		qsig = PluginProcess(self.conf.c_dir, [cmd_str, req]).run_query_process(pargs, req, rquery)
		return qsig
		
	def rebuild():
		NOT_IMPLEMENTED(__name__, __func__)

	def conf_is_open(self):
		return self.conf != None
	def conf_is_ready(self):
		return self.conf.is_ready()
		

class QueryUiBase(QObject):
	def __init__(self):
		QObject.__init__(self)

from PyQt4.QtGui import QMessageBox

class QuerySignal(QObject):
	sig_result = pyqtSignal(str, list)
	sig_result_dbg = pyqtSignal(str, str, str)
	sig_rebuild = pyqtSignal()
	sig_query_fl = pyqtSignal(list)

	def __init__(self):
		QObject.__init__(self)

	def _relevancy_sort(self, hfile, res):
		pt = []
		pd = {}
		p = hfile
		(pre, ext) = os.path.splitext(hfile)
		c = None
		while p != c:
			e = [p, [], []]
			pt += [e]
			pd[p] = e
			c = p
			p = os.path.dirname(p)
		for line in res:
			f = line[1]
			d = os.path.dirname(f)
			p = f
			while p not in pd:
				p = os.path.dirname(p)
			e = pd[p]
			if p in [f, d]:
				e[1].append(line)
			else:
				e[2].append(line)
		for e in pt:
			e[1] = sorted(e[1], key=lambda li: li[1])
			e[2] = sorted(e[2], key=lambda li: li[1])
		pre = pre + '.*'
		e0 = []
		e1 = []
		for e in pt[1][1]:
			if re.match(pre, e[1]):
				e0 += [e]
			else:
				e1 += [e]
		pt[0][1] += e0
		pt[1][1] = e1

		res1 = []
		res2 = []
		for e in pt:
			res1 += e[1]
			res2 += e[2]
		res = res1 + res2
		return res

	def relevancy_sort(self, res):
		if os.getenv('RELEVANCY_SORT', 1) == 0:
			return res
		hint_file = None
		try:
			hint_file = self.rquery['hint_file']
		except:
			pass
		if not hint_file:
			return res
		if not os.path.isabs(hint_file):
			print 'BUG: relevancy_sort: not abs path:', hint_file
			return res
		if len(res) > 10000:
			return res
		return self._relevancy_sort(hint_file, res)

	def emit_result(self, res):
		res = self.relevancy_sort(res)
		self.sig_result.emit(self.sym, res)

class PluginProcessBase(QObject):
	proc_list = []

	def __init__(self, wdir):
		QObject.__init__(self)
		
		PluginProcess.proc_list.append(self)
		self.is_rebuild = False
		self.is_query_fl = False

		self.sig = QuerySignal()

		self.proc = QProcess()
		self.proc.finished.connect(self._finished_cb)
		self.proc.error.connect(self._error_cb)

		self.proc.setWorkingDirectory(wdir)
		self.wdir = wdir

	def _cleanup(self):
		PluginProcess.proc_list.remove(self)
		if self.err_str != '':
			s = '<b>' + self.p_cmd + '</b><p>' + '<p>'.join(self.err_str.splitlines())
			QMessageBox.warning(None, "Seascope", s, QMessageBox.Ok)
		if self.res != '':
			s = '<b>' + self.p_cmd + '</b><p>Summary<p>' + self.res
			QMessageBox.information(None, "Seascope", s, QMessageBox.Ok)

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
		#print 'cmd:', self.p_cmd
		if self.is_rebuild:
			self.res = res
			self.sig.sig_rebuild.emit()
		elif self.is_query_fl:
			self.res = ''
			res = self.parse_query_fl(res)
			self.sig.sig_query_fl.emit(res)
		else:
			self.res = ''
			self.sig.sig_result_dbg.emit(self.p_cmd, res, self.err_str)
			try:
				res = self.parse_result(res, self.sig)
			except Exception as e:
				print e
				res = [['', '', '', 'error while parsing output of: ' + self.p_cmd]]
			if res != None:
				self.sig.emit_result(res)

		self._cleanup()

	def run_query_process(self, pargs, sym, rquery=None):
		self.sig.sym = sym
		self.sig.rquery = rquery
		self.p_cmd = ' '.join(pargs)
		if os.getenv('SEASCOPE_DEBUG'):
			print self.p_cmd
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
		#print 'cmd:', pargs
		self.sig.sig_rebuild.connect(CtagsCache.flush)
		return self.sig.sig_rebuild

	def run_query_fl(self, pargs):
		self.is_query_fl = True
		self.p_cmd = ' '.join(pargs)
		self.proc.start(pargs[0], pargs[1:])
		if self.proc.waitForStarted() == False:
			return None
		return self.sig.sig_query_fl

	def parse_query_fl(self, text):
		fl = []
		for f in re.split('\r?\n', text.strip()):
			if f == '':
				continue
			fl.append(os.path.join(self.wdir, f))
		return fl

class PluginProcess(PluginProcessBase):
	def __init__(self, wdir, rq):
		PluginProcessBase.__init__(self, wdir)
		if rq == None:
			rq = ['', '']
		self.cmd_str = rq[0]
		self.req = rq[1]

	def parse_result(self, text, sig):
		text = re.split('\r?\n', text)

		res = []
		if self.cmd_str == 'GREP':
			for line in text:
				if line == '':
					continue
				line = ['<unknown>'] + line.split(':', 2)
				res.append(line)
		else:
			assert(false)
			res.append(['', '', '', 'PluginProcess.parse_result: FAILED'])
			return res

		qsig = CtagsCache.CtagsThread(sig).apply_fix(self.cmd_str, res, ['<unknown>'])
		return qsig

if __name__ == '__main__':
	import sys

	def slot_result(sym, res):
		print 'slot_result:    ', [str(sym), res]
		sys.exit(0)
	def slot_result_dbg(cmd, res, err_str):
		print 'slot_result_dbg:', [str(cmd), str(res).strip().split('\n'), str(err_str)]
	def slot_rebuild():
		print 'slot_rebuild'

	from PyQt4.QtCore import QCoreApplication
	app = QCoreApplication(sys.argv)

	qsig = PluginProcess('.').run_query_process(['ls'], 'ls')
	#qsig = PluginProcess('/home/anil/prj/ss/lin').run_query_process(['cscope', '-q', '-k', '-L', '-d', '-0', 'vdso'], 'ls')
	if qsig == None:
		sys.exit(-1)
	qsig[0].connect(slot_result)
	qsig[1].connect(slot_result_dbg)

	app.exec_()
