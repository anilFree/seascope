#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os, string, re

from ..PluginBase import PluginFeatureBase, ProjectBase, ConfigBase, QueryBase
from ..PluginBase import PluginProcess
from ..CtagsCache import CtagsThread


class GtagsFeature(PluginFeatureBase):
	def __init__(self):
		PluginFeatureBase.__init__(self)

		self.feat_desc = [
			['REF',	'-r'],
			['DEF',	''],
			#['<--',	'2'],
			['-->',	'-r'],
			#[	['TXT',	'4'],
			['GREP','-g'],
			['FIL',	'-P'],
			['INC',	'-g'],

			['QDEF', ''],
			['CTREE','12'],

			['CLGRAPH', '13'],
			['CLGRAPHD', '14'],
			['FFGRAPH', '14'],

			['UPD', '25'],
		]

		self.ctree_query_args = [
			['-->',	'--> F', 'Calling tree'			],
			#['<--',	'F -->', 'Called tree'			],
			['REF',	'==> F', 'Advanced calling tree'	],
		]
		
	def query_dlg_cb(self, req, cmd_str, in_opt):
		if req != '' and in_opt['substring']:
			req = '.*' + req + '.*'
		opt = None
		if in_opt['ignorecase']:
			opt = '-i'
		res = (cmd_str, req, opt)
		return res

class ConfigGtags(ConfigBase):
	def __init__(self):
		ConfigBase.__init__(self, 'gtags')

class ProjectGtags(ProjectBase):
	def __init__(self):
		ProjectBase.__init__(self)

	@staticmethod
	def _prj_new_or_open(conf):
		prj = ProjectGtags()
		prj.feat = GtagsFeature()
		prj.conf = conf
		prj.qry = QueryGtags(prj.conf, prj.feat)

		return (prj)

	@staticmethod
	def prj_new(proj_args):
		d = proj_args[0]
		prj = ProjectGtags.prj_open(d)
		return None

	@staticmethod
	def prj_open(proj_path):
		conf = ConfigGtags()
		conf.proj_open(proj_path)
		prj = ProjectGtags._prj_new_or_open(conf)
		return (prj)


class GtProcess(PluginProcess):
	def __init__(self, wdir, rq):
		PluginProcess.__init__(self, wdir, rq)
		self.name = 'gtags process'

	def parse_result(self, text, sig):
		text = re.split('\r?\n', text)
		if self.cmd_str == 'FIL':
			res = [ ['',  line.split(' ')[0], '', '' ] for line in text if line != '' ]
			return res
		res = []
		for line in text:
			if line == '':
				continue
			line = line.split(' ', 3)
			line = ['<unknown>', line[0], line[2], line[3]]
			res.append(line)

		CtagsThread(sig).apply_fix(self.cmd_str, res, ['<unknown>'])

		return None

class QueryGtags(QueryBase):
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
		if opt == None or opt == '':
			opt = []
		else:
			opt = opt.split()
		cmd_opt = self.feat.cmd_str2id[cmd_str]
		pargs = [ 'global', '-a', '--result=cscope', '-x' ] + opt
		if cmd_opt != '':
			pargs += [ cmd_opt ]
		pargs += [ '--', req ]
		
		qsig = GtProcess(self.conf.c_dir, [cmd_str, req]).run_query_process(pargs, req, rquery)
		return qsig

	def rebuild(self):
		if (not self.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		if (os.path.exists(os.path.join(self.conf.c_dir, 'GTAGS'))):
			pargs = [ 'global', '-u' ]
		else:
			pargs = [ 'gtags', '-i' ]
		qsig = GtProcess(self.conf.c_dir, None).run_rebuild_process(pargs)
		return qsig

	def query_fl(self):
		if not os.path.exists(os.path.join(self.conf.c_dir, 'GTAGS')):
			return []
		pargs = [ 'global', '-P', '-a' ]
		qsig = GtProcess(self.conf.c_dir, None).run_query_fl(pargs)
		return qsig

	def gt_is_open(self):
		return self.conf != None
	def gt_is_ready(self):
		return self.conf.is_ready()
