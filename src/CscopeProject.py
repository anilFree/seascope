#!/usr/bin/python

from CscopeManager import CsProcess

import os, string

class CsConfig:
	def __init__(self):
		self.cs_dir = ''
		self.cs_opt = ''
		self.cs_list = []

	def get_proj_name(self):
		return os.path.split(self.cs_dir)[1]
	def get_proj_src_files(self):
		return self.cs_list

	def read_cscope_files(self):
		config_file = os.path.join(self.cs_dir, 'cscope.files')
		if (not os.path.exists(config_file)):
			return
		cf = open(config_file, 'r')
		fl = []
		for f in cf:
			f = f[:-1]
			fl.append(f)
		cf.close()
		self.cs_list = fl

	def write_cscope_files(self):
		if (len(self.cs_list) <= 0):
			return
		config_file = os.path.join(self.cs_dir, 'cscope.files')
		cf = open(config_file, 'w')
		for f in self.cs_list:
			cf.write(f + '\n')
		cf.close()

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
		self.read_cscope_files()

	def write_config(self):
		self.write_seascope_opt()
		self.write_cscope_files()

	def proj_start(self):
		cs_args = string.join(self.cs_opt)
		#print "pp:", self.cs_dir, cs_args
		if (len(self.cs_list) > 0):
			CsProcess.cs_setup(cs_args, self.cs_dir)

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
		CsProcess.cs_setup_clear()

	def get_proj_conf(self):
		self.read_cscope_files()
		return (self.cs_dir, self.cs_opt, self.cs_list)

	def is_ready(self):
		return len(self.cs_list) > 0

class CsQuery:
	conf = None

	@staticmethod
	def cs_proj_new(args):
		if (CsQuery.conf != None):
			print 'FATAL: cs_proj_open: pm = None'
			sys.exit(-1)
		CsQuery.conf = CsConfig()
		CsQuery.conf.proj_new(args)

	@staticmethod
	def cs_get_proj_dir():
		return CsQuery.conf.cs_dir
	@staticmethod
	def cs_get_proj_name():
		return CsQuery.conf.get_proj_name()
	@staticmethod
	def cs_get_proj_src_files():
		return CsQuery.conf.get_proj_src_files()

	@staticmethod
	def cs_proj_open(proj_path):
		if (CsQuery.conf != None):
			print 'FATAL: cs_proj_open: pm = None'
			sys.exit(-1)
		CsQuery.conf = CsConfig()
		CsQuery.conf.proj_open(proj_path)

	@staticmethod
	def cs_proj_close():
		if (CsQuery.conf != None):
			CsQuery.conf.proj_close()
		CsQuery.conf = None

	@staticmethod
	def cs_query(cmd_id, req, opt = None):
		if (not CsQuery.conf or not CsQuery.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		return CsProcess.cs_query(cmd_id, req, opt)
	@staticmethod
	def cs_rebuild():
		if (not CsQuery.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		return CsProcess.cs_rebuild()

	@staticmethod
	def cs_is_open():
		return CsQuery.conf != None
	@staticmethod
	def cs_is_ready():
		return CsQuery.conf.is_ready()
		
	@staticmethod
	def cs_get_proj_conf():
		return CsQuery.conf.get_proj_conf()
		
	@staticmethod
	def cs_proj_update(proj_args):
		CsQuery.conf.proj_update(proj_args)
