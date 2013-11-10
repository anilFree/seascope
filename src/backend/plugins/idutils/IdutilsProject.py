#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import sys, os, string, re
from PyQt4.QtCore import *

from ..PluginBase import PluginFeatureBase, ProjectBase, ConfigBase, QueryBase

class IdutilsFeature(PluginFeatureBase):
	def __init__(self):
		PluginFeatureBase.__init__(self)

		self.feat_desc = [
			['REF',     ''],
			['DEF',     ''],
			#['<--',    '2'],
			['-->',     '3'],
			#['TXT',    '4'],
			['GREP',    ''],
			['FIL',     ''],
			['INC',     '8'],

			['QDEF',    ''],
			['CTREE',   '12'],

			['CLGRAPH', '13'],
			['CLGRAPHD','14'],
			['FFGRAPH', '14'],

			['UPD',    '25'],
		]

		self.ctree_query_args = [
			['-->',	'--> F', 'Calling tree'			],
			#['<--',	'F -->', 'Called tree'			],
			['REF',	'==> F', 'Advanced calling tree'	],
		]

	def query_dlg_cb(self, req, cmd_str, in_opt):
		opt = []
		if cmd_str != 'TXT' and req != '' and in_opt['substring']:
			opt.append('substring')
			if cmd_str == 'FIL':
				req = '*' + req + '*'
			else:
				req = '.*' + req + '.*'
		if in_opt['ignorecase']:
			opt.append('ignorecase')

		res = (cmd_str, req, opt)
		return res



class ConfigIdutils(ConfigBase):
	def __init__(self):
		ConfigBase.__init__(self, 'idutils')

class ProjectIdutils(ProjectBase):
	def __init__(self):
		ProjectBase.__init__(self)

	@staticmethod
	def _prj_new_or_open(conf):
		prj = ProjectIdutils()
		prj.feat = IdutilsFeature()
		prj.conf = conf
		prj.qry = QueryIdutils(prj.conf, prj.feat)
		return (prj)

	@staticmethod
	def prj_new(proj_args):
		d = proj_args[0]
		prj = ProjectIdutils.prj_open(d)
		return prj

	@staticmethod
	def prj_open(proj_path):
		conf = ConfigIdutils()
		conf.proj_open(proj_path)
		prj = ProjectIdutils._prj_new_or_open(conf)
		return (prj)


from ..PluginBase import PluginProcess
from ..CtagsCache import CtagsThread

class IdCtagsThread(CtagsThread):
	def __init__(self, sig):
		CtagsThread.__init__(self, sig)

	def ctags_bsearch(self, ct, n):
		m = CtagsThread.ctags_bsearch(self, ct, n)
		return m

	def parse_result(self, res, sig):
		res = self._filter_res(res, sig)
		return res

class IdProcess(PluginProcess):
	def __init__(self, wdir, rq):
		PluginProcess.__init__(self, wdir)
		self.name = 'idutils process'
		if rq == None:
			rq = ['', '']
		self.cmd_str = rq[0]
		self.req = rq[1]


	def parse_result(self, text, sig):
		#from datetime import datetime
		#t1 = datetime.now()

		text = re.split('\r?\n', text)

		#t2 = datetime.now()
		#print 'parse-split', t2 - t1

		if self.cmd_str == 'FIL':
			res = [ ['',  os.path.join(self.wdir, line), '', '' ] for line in text if line != '' ]
			return res

		res = []
		if self.cmd_str == 'GREP':
			for line in text:
				if line == '':
					continue
				line = ['<unknown>'] + line.split(':', 2)
				res.append(line)
		else:
			for line in text:
				if line == '':
					continue
				line = line.split(':', 2)
				line = ['<unknown>', os.path.join(self.wdir, line[0]), line[1], line[2]]
				res.append(line)

		#t3 = datetime.now()
		#print 'parse-loop', t3 - t2

		IdCtagsThread(sig).apply_fix(self.cmd_str, res, ['<unknown>'])

		return None

class QueryIdutils(QueryBase):
	def __init__(self, conf, feat):
		QueryBase.__init__(self)
		self.conf = conf
		self.feat = feat

	def query(self, rquery):
		if (not self.conf):
		#or not self.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		cmd_str = rquery['cmd']
		req     = rquery['req']
		opt     = rquery['opt']
		if opt == None:
			opt = []
		
		pargs = ['lid', '-R', 'grep']
		if cmd_str == 'FIL':
			pargs = ['fnid', '-S', 'newline']
		elif cmd_str == 'GREP':
			pargs = ['grep', '-E', '-R', '-n', '-I']
		#elif cmd_str == 'TXT':
			#pargs += ['-l']
		elif 'substring' in opt:
			#req = '.*' + req + '.*'
			#pargs += ' -s'
			pass
		elif cmd_str in ['-->', '<--']:
			pargs += ['-l']

		if cmd_str != 'FIL':
			if 'ignorecase' in opt:
				pargs += ['-i']
		pargs += [ '--', req ]
		if cmd_str == 'GREP':
			pargs += [self.conf.c_dir]
		qsig = IdProcess(self.conf.c_dir, [cmd_str, req]).run_query_process(pargs, req, rquery)
		return qsig

	def rebuild(self):
		if (not self.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		pargs = os.getenv('SEASCOPE_IDUTILS_MKID_CMD', '').strip().split()
		if not len(pargs):
			pargs = [ 'mkid', '-s' ]
		qsig = IdProcess(self.conf.c_dir, None).run_rebuild_process(pargs)
		return qsig

	def query_fl(self):
		if not os.path.exists(os.path.join(self.conf.c_dir, 'ID')):
			return []
		pargs = [ 'fnid', '-S', 'newline', '-f', 'ID' ]
		qsig = IdProcess(self.conf.c_dir, None).run_query_fl(pargs)
		return qsig

	def id_is_open(self):
		return self.conf != None
	def id_is_ready(self):
		return self.conf.is_ready()
