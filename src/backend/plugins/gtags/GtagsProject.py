#!/usr/bin/python

import os, string
from PyQt4.QtCore import *

from ..PluginBase import ProjectBase, ConfigBase, QueryBase
from GtagsProjectUi import QueryUiGtags

from .. import PluginHelper

class ConfigGtags(ConfigBase):
	def __init__(self):
		ConfigBase.__init__(self)

		self.gt_dir = ''
		self.gt_opt = ''
		self.gt_list = []

	def get_proj_name(self):
		return os.path.split(self.gt_dir)[1]
	def get_proj_src_files(self):
		fl = self.gt_list
		return fl

	#def read_gt_files_common(self, filename):
		#fl = []
		#config_file = os.path.join(self.gt_dir, filename)
		#if (os.path.exists(config_file)):
			#cf = open(config_file, 'r')
			#for f in cf:
				#f = f[:-1]
				#fl.append(f)
			#cf.close()
		#return fl

	#def read_gt_files(self):
		#self.gt_list = self.read_gt_files_common('cscope.files')

	#def write_gt_files_common(self, filename, fl):
		#if (len(fl) <= 0):
			#return
		#config_file = os.path.join(self.gt_dir, filename)
		#cf = open(config_file, 'w')
		#for f in fl:
			#cf.write(f + '\n')
		#cf.close()

	#def write_gt_files(self):
		#self.write_gt_files_common("cscope.files", self.gt_list)

	#def get_config_file(self):
		#config_file = 'seascope.opt'
		#return os.path.join(self.gt_dir, config_file)

	#def read_seascope_opt(self):
		#config_file = self.get_config_file()
		#if (not os.path.exists(config_file)):
			#return
		#cf = open(config_file, 'r')
		#for line in cf:
			#line = line.split('=', 1)
			#key = line[0].strip()
			#if (key == 'gt_opt'):
				#self.gt_opt = line[1].split()
		#cf.close()
		
	#def write_seascope_opt(self):
		#config_file = self.get_config_file()
		#cf = open(config_file, 'w')
		#cf.write('gt_opt' + '=' + string.join(self.gt_opt)+ '\n')
		#cf.close()
		
	#def read_config(self):
		#self.read_seascope_opt()
		#self.read_gt_files()

	#def write_config(self):
		#self.write_seascope_opt()
		#self.write_gt_files()

	def proj_start(self):
		gt_args = string.join(self.gt_opt)

	def proj_open(self, proj_path):
		self.gt_dir = proj_path
		print self.gt_dir
		#self.read_config()
		self.proj_start()

	def proj_update(self, proj_args):
		self.proj_new(proj_args)
		
	def proj_new(self, proj_args):
		self.proj_args = proj_args
		(self.gt_dir, self.gt_opt, self.gt_list) = proj_args
		#self.write_config()
		self.proj_start()

	def proj_close(self):
		pass

	def get_proj_conf(self):
		self.read_gt_files()
		return (self.gt_dir, self.gt_opt, self.gt_list)

	def is_ready(self):
		return True

class ProjectGtags(ProjectBase):
	def __init__(self):
		ProjectBase.__init__(self)

	@staticmethod
	def _prj_new_or_open(conf):
		prj = ProjectGtags()
		prj.conf = conf
		prj.qry = QueryGtags(prj.conf)
		prj.qryui = QueryUiGtags(prj.qry)

		PluginHelper.file_view_update(prj.conf.get_proj_src_files())
		return (prj)

	@staticmethod
	def prj_new():
		proj_args = QueryUiGtags.prj_show_settings_ui(None)
		if (proj_args == None):
			return None

		conf = ConfigGtags()
		conf.proj_new(proj_args)
		prj = ProjectGtags._prj_new_or_open(conf)
		return (prj)

	@staticmethod
	def prj_open(proj_path):
		conf = ConfigGtags()
		conf.proj_open(proj_path)
		prj = ProjectGtags._prj_new_or_open(conf)
		return (prj)

	def prj_close(self):
		if (self.conf != None):
			self.conf.proj_close()
		self.conf = None

	def prj_dir(self):
		return self.conf.gt_dir
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
		proj_args = QueryUiGtags.prj_show_settings_ui(proj_args)
		if (proj_args == None):
			return False
		self.prj_update_conf(proj_args)
		return True

from ..PluginBase import PluginProcess

class GtProcess(PluginProcess):
	def __init__(self, wdir):
		PluginProcess.__init__(self, wdir)
		self.name = 'gtags process'

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
		return res

class QueryGtags(QueryBase):
	def __init__(self, conf):
		QueryBase.__init__(self)
		self.conf = conf

	def gt_query(self, cmd_id, req, opt = None):
		print cmd_id, req, opt
		if (not self.conf):
		#or not self.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		pargs = [ 'global', '-a', '--result=cscope', ' -x ', str(cmd_id), req ]
		qsig = GtProcess(self.conf.gt_dir).run_query_process(pargs, req)
		return qsig

	def gt_rebuild(self):
		if (not self.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		if (os.path.exists(os.path.join(self.conf.gt_dir, 'GTAGS'))):
			pargs = [ 'global', '-u' ]
		else:
			pargs = [ 'gtags', '-i' ]
		qsig = GtProcess(self.conf.gt_dir).run_rebuild_process(pargs)
		return qsig

	def gt_is_open(self):
		return self.conf != None
	def gt_is_ready(self):
		return self.conf.is_ready()
