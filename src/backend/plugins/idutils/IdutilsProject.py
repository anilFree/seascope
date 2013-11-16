#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import sys, os, string, re

from ..PluginBase import PluginFeatureBase, ProjectBase, ConfigBase, QueryBase
from ..PluginBase import PluginProcess
from ..CtagsCache import CtagsThread


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


class IdProcess(PluginProcess):
	def __init__(self, wdir, rq):
		PluginProcess.__init__(self, wdir, rq)
		self.name = 'idutils process'

	def parse_result(self, text, sig):
		if self.cmd_str in ['GREP']:
			return PluginProcess.parse_result(self, text, sig)

		#from datetime import datetime
		#t1 = datetime.now()

		text = re.split('\r?\n', text)

		#t2 = datetime.now()
		#print 'parse-split', t2 - t1

		if self.cmd_str == 'FIL':
			res = [ ['',  os.path.join(self.wdir, line), '', '' ] for line in text if line != '' ]
			return res

		res = []
		for line in text:
			if line == '':
				continue
			line = line.split(':', 2)
			line = ['<unknown>', os.path.join(self.wdir, line[0]), line[1], line[2]]
			res.append(line)

		#t3 = datetime.now()
		#print 'parse-loop', t3 - t2

		CtagsThread(sig).apply_fix(self.cmd_str, res, ['<unknown>'])

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
		if cmd_str in ['GREP']:
			return QueryBase.query(self, rquery)
		req     = rquery['req']
		opt     = rquery['opt']
		if opt == None:
			opt = []

		pargs = ['lid', '-R', 'grep']
		if cmd_str == 'FIL':
			pargs = ['fnid', '-S', 'newline']
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
