#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os, string, re

from ..PluginBase import PluginFeatureBase, ProjectBase, ConfigBase, QueryBase
from ..PluginBase import PluginProcess


class CscopeFeature(PluginFeatureBase):
	def __init__(self):
		PluginFeatureBase.__init__(self)

		self.feat_desc = [
			['REF',	'0'],
			['DEF',	'1'],
			['<--',	'2'],
			['-->',	'3'],
			['TXT',	'4'],
			['GREP','5'],
			['FIL',	'7'],
			['INC',	'8'],

			['QDEF', '11'],
			['CTREE','12'],

			['CLGRAPH', '13'],
			['CLGRAPHD', '14'],
			['FFGRAPH', '14'],

			['UPD', '25'],
		]

		self.ctree_query_args = [
			['-->',	'--> F', 'Calling tree'			],
			['<--',	'F -->', 'Called tree'			],
			['REF',	'==> F', 'Advanced calling tree'	],
		]
				
class ConfigCscope(ConfigBase):
	def __init__(self):
		ConfigBase.__init__(self, 'cscope')
		self.c_opt = []

	def read_cs_files_common(self, filename):
		fl = []
		config_file = os.path.join(self.c_dir, filename)
		if (os.path.exists(config_file)):
			cf = open(config_file, 'r')
			for f in cf:
				f = f[:-1]
				fl.append(f)
			cf.close()
		return fl

	def read_cs_files(self):
		self.c_flist = self.read_cs_files_common('cscope.files')

	def write_cs_files_common(self, filename, fl):
		if (len(fl) <= 0):
			return
		config_file = os.path.join(self.c_dir, filename)
		cf = open(config_file, 'w')
		for f in fl:
			cf.write(f + '\n')
		cf.close()

	def write_cs_files(self):
		self.write_cs_files_common("cscope.files", self.c_flist)

	def get_config_file(self):
		config_file = 'seascope.opt'
		return os.path.join(self.c_dir, config_file)

	def read_seascope_opt(self):
		config_file = self.get_config_file()
		if (not os.path.exists(config_file)):
			return
		cf = open(config_file, 'r')
		for line in cf:
			line = line.split('=', 1)
			key = line[0].strip()
			if (key == 'c_opt'):
				self.c_opt = line[1].split()
		cf.close()
		
	def write_seascope_opt(self):
		config_file = self.get_config_file()
		cf = open(config_file, 'w')
		cf.write('c_opt' + '=' + string.join(self.c_opt)+ '\n')
		cf.close()
		
	def read_config(self):
		self.read_seascope_opt()
		self.read_cs_files()

	def write_config(self):
		self.write_seascope_opt()
		self.write_cs_files()

	def is_ready(self):
		return len(self.c_flist) > 0

class ProjectCscope(ProjectBase):
	def __init__(self):
		ProjectBase.__init__(self)

	@staticmethod
	def _prj_new_or_open(conf):
		prj = ProjectCscope()
		prj.feat = CscopeFeature()
		prj.conf = conf
		prj.qry = QueryCscope(prj.conf, prj.feat)
		
		return (prj)

	@staticmethod
	def prj_new(proj_args):
		conf = ConfigCscope()
		conf.proj_new(proj_args)
		prj = ProjectCscope._prj_new_or_open(conf)
		return (prj)

	@staticmethod
	def prj_open(proj_path):
		conf = ConfigCscope()
		conf.proj_open(proj_path)
		prj = ProjectCscope._prj_new_or_open(conf)
		return (prj)

	def prj_settings_update(self, proj_args):
		assert proj_args
		self.prj_update_conf(proj_args)
		return True


class CsProcess(PluginProcess):
	def __init__(self, wdir, rq):
		PluginProcess.__init__(self, wdir, rq)
		self.name = 'cscope process'

	def parse_result(self, text, sig):
		text = re.split('\r?\n', text)
		if self.cmd_str == 'FIL':
			res = [ ['', line[0], '', ''] for line in text if line != '' ]
			return res
		res = []
		for line in text:
			if line == '':
				continue
			line = line.split(' ', 3)
			line = [line[1], line[0], line[2], line[3]]
			res.append(line)
		return res

class QueryCscope(QueryBase):
	def __init__(self, conf, feat):
		QueryBase.__init__(self)
		self.conf = conf
		self.feat = feat

	def query(self, rquery):
		if (not self.conf or not self.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		cmd_str = rquery['cmd']
		req     = rquery['req']
		opt     = rquery['opt']
		cmd_id = self.feat.cmd_str2id[cmd_str]

		if opt == None:
			opt = []
		opt_args = []
		if 'substring' in opt:
			req = '.*' + req + '.*'
		if 'ignorecase' in opt:
			opt_args += ['-C'];

		pargs  = [ 'cscope' ] + self.conf.c_opt + opt_args + [ '-L', '-d',  '-' + str(cmd_id), req ]
		qsig = CsProcess(self.conf.c_dir, [cmd_str, req]).run_query_process(pargs, req, rquery)
		return qsig

	def rebuild(self):
		if (not self.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		pargs = [ 'cscope' ] + self.conf.c_opt + [ '-L' ]
		qsig = CsProcess(self.conf.c_dir, None).run_rebuild_process(pargs)
		return qsig

	def query_fl(self):
		fl = self.conf.get_proj_src_files()
		return fl

	def cs_is_open(self):
		return self.conf != None
	def cs_is_ready(self):
		return self.conf.is_ready()
