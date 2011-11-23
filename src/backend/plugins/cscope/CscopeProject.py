#!/usr/bin/python

from CscopeManager import CsProcess

import os, string
from PyQt4.QtCore import *

from ..PluginBase import ProjectBase, ConfigBase, QueryBase
from CscopeProjectUi import QueryUiCscope

class ConfigCscope(ConfigBase):
	def __init__(self):
		ConfigBase.__init__(self)

		self.cs_dir = ''
		self.cs_opt = ''
		self.cs_list = []

	def get_proj_name(self):
		return os.path.split(self.cs_dir)[1]
	def get_proj_src_files(self):
		fl = self.cs_list
		return fl

	def read_cs_files_common(self, filename):
		fl = []
		config_file = os.path.join(self.cs_dir, filename)
		if (os.path.exists(config_file)):
			cf = open(config_file, 'r')
			for f in cf:
				f = f[:-1]
				fl.append(f)
			cf.close()
		return fl

	def read_cs_files(self):
		self.cs_list = self.read_cs_files_common('cscope.files')

	def write_cs_files_common(self, filename, fl):
		if (len(fl) <= 0):
			return
		config_file = os.path.join(self.cs_dir, filename)
		cf = open(config_file, 'w')
		for f in fl:
			cf.write(f + '\n')
		cf.close()

	def write_cs_files(self):
		self.write_cs_files_common("cscope.files", self.cs_list)

	def get_config_file(self):
		config_file = 'seascope.opt'
		return os.path.join(self.cs_dir, config_file)

	def read_seascope_opt(self):
		config_file = self.get_config_file()
		if (not os.path.exists(config_file)):
			return
		cf = open(config_file, 'r')
		for line in cf:
			line = line.split('=', 1)
			key = line[0].strip()
			if (key == 'cs_opt'):
				self.cs_opt = line[1].split()
		cf.close()
		
	def write_seascope_opt(self):
		config_file = self.get_config_file()
		cf = open(config_file, 'w')
		cf.write('cs_opt' + '=' + string.join(self.cs_opt)+ '\n')
		cf.close()
		
	def read_config(self):
		self.read_seascope_opt()
		self.read_cs_files()

	def write_config(self):
		self.write_seascope_opt()
		self.write_cs_files()

	def proj_start(self):
		cs_args = string.join(self.cs_opt)

	def proj_open(self, proj_path):
		self.cs_dir = proj_path
		self.read_config()
		self.proj_start()

	def proj_update(self, proj_args):
		self.proj_new(proj_args)
		
	def proj_new(self, proj_args):
		self.proj_args = proj_args
		(self.cs_dir, self.cs_opt, self.cs_list) = proj_args
		self.write_config()
		self.proj_start()

	def proj_close(self):
		pass

	def get_proj_conf(self):
		self.read_cs_files()
		return (self.cs_dir, self.cs_opt, self.cs_list)

	def is_ready(self):
		return len(self.cs_list) > 0

class ProjectCscope(ProjectBase):
	def __init__(self):
		ProjectBase.__init__(self)

	@staticmethod
	def _prj_new_or_open(conf):
		prj = ProjectCscope()
		prj.conf = conf
		prj.qry = QueryCscope(prj.conf)
		prj.qryui = QueryUiCscope(prj.qry)
		return (prj)

	@staticmethod
	def prj_new():
		proj_args = QueryUiCscope.prj_show_settings_ui(None)
		if (proj_args == None):
			return None

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

	def prj_close(self):
		if (self.conf != None):
			self.conf.proj_close()
		self.conf = None

	def prj_dir(self):
		return self.conf.cs_dir
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
	def prj_settings_trigger(self):
		proj_args = self.prj_conf()
		proj_args = QueryUiCscope.prj_show_settings_ui(proj_args)
		if (proj_args == None):
			return False
		self.prj_update_conf(proj_args)
		return True

from ..PluginBase import PluginProcess

class CsProcess(PluginProcess):
	def __init__(self, wdir):
		PluginProcess.__init__(self, wdir)
		self.name = 'cscope process'

	def parse_result(self, text):
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

class QueryCscope(QueryBase):
	def __init__(self, conf):
		QueryBase.__init__(self)
		self.conf = conf

	def cs_query(self, cmd_id, req, opt = None):
		if (not self.conf or not self.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		if opt == None:
			opt = ''
		pargs = 'cscope ' + self.conf.cs_opt + ' -L -d ' + opt + ' -' + str(cmd_id) + ' ' + req
		qsig = CsProcess(self.conf.cs_dir).run_query_process(pargs, req)
		return qsig

	def cs_rebuild(self):
		if (not self.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		pargs = 'cscope ' + self.conf.cs_opt + ' -L'
		qsig = CsProcess(self.conf.cs_dir).run_rebuild_process(pargs)
		return qsig

	def cs_is_open(self):
		return self.conf != None
	def cs_is_ready(self):
		return self.conf.is_ready()
