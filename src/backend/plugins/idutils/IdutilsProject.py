#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import sys, os, string, re
from PyQt4.QtCore import *

from ..PluginBase import ProjectBase, ConfigBase, QueryBase
from IdutilsProjectUi import QueryUiIdutils

class ConfigIdutils(ConfigBase):
	def __init__(self):
		ConfigBase.__init__(self)

		self.id_dir = ''
		self.id_opt = ''
		self.id_list = []

	def get_proj_name(self):
		return os.path.split(self.id_dir)[1]
	def get_proj_src_files(self):
		return []

	def proj_start(self):
		id_args = string.join(self.id_opt)

	def proj_open(self, proj_path):
		self.id_dir = proj_path
		self.proj_start()

	def proj_update(self, proj_args):
		self.proj_new(proj_args)
		
	def proj_new(self, proj_args):
		self.proj_args = proj_args
		(self.id_dir, self.id_opt, self.id_list) = proj_args
		self.proj_start()

	def proj_close(self):
		pass

	def get_proj_conf(self):
		return (self.id_dir, self.id_opt, self.id_list)

	def is_ready(self):
		return True

class ProjectIdutils(ProjectBase):
	def __init__(self):
		ProjectBase.__init__(self)

	@staticmethod
	def _prj_new_or_open(conf):
		prj = ProjectIdutils()
		prj.conf = conf
		prj.qry = QueryIdutils(prj.conf)
		prj.qryui = QueryUiIdutils(prj.qry)
		return (prj)

	@staticmethod
	def prj_new():
		from PyQt4.QtGui import QFileDialog
		fdlg = QFileDialog(None, "Choose source code directory")
		fdlg.setFileMode(QFileDialog.Directory);
		#fdlg.setDirectory(self.pd_path_inp.text())
		if fdlg.exec_():
			d = fdlg.selectedFiles()[0];
			d = str(d)
			if not d:
				return None
			d = os.path.normpath(d)
			if d == '' or not os.path.isabs(d):
				return None
			prj = ProjectIdutils.prj_open(d)
			prj.qryui.do_rebuild()
			return prj
		return None

	@staticmethod
	def prj_open(proj_path):
		conf = ConfigIdutils()
		conf.proj_open(proj_path)
		prj = ProjectIdutils._prj_new_or_open(conf)
		return (prj)

	def prj_close(self):
		if (self.conf != None):
			self.conf.proj_close()
		self.conf = None

	def prj_dir(self):
		return self.conf.id_dir
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
		proj_args = QueryUiIdutils.prj_show_settings_ui(proj_args)
		#if (proj_args == None):
			#return False
		#self.prj_update_conf(proj_args)
		#return True
		return False

from ..PluginBase import PluginProcess
from .. import PluginHelper
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
	def __init__(self, conf):
		QueryBase.__init__(self)
		self.conf = conf

		self.id_file_list_update()

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
		elif cmd_str == 'TXT':
			pargs += ['-l']
		elif 'substring' in opt:
			#req = '.*' + req + '.*'
			#pargs += ' -s'
			pass
		elif cmd_str in ['-->', '<--']:
			pargs += ['-l']
		pargs += [ req ]
		qsig = IdProcess(self.conf.id_dir, [cmd_str, req]).run_query_process(pargs, req, rquery)
		return qsig

	def rebuild(self):
		if (not self.conf.is_ready()):
			print "pm_query not is_ready"
			return None
		pargs = [ 'mkid', '-s' ]
		qsig = IdProcess(self.conf.id_dir, None).run_rebuild_process(pargs)
		qsig.connect(self.id_file_list_update)
		return qsig

	def id_file_list_update(self):
		id_file = os.path.join(self.conf.id_dir, 'ID')
		if not os.path.exists(id_file):
			return
		fl = []
		try:
			import subprocess
			pargs = [ 'fnid', '-S', 'newline', '-f', id_file ]
			proc = subprocess.Popen(pargs, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			(out_data, err_data) = proc.communicate()
			fl = re.split('\r?\n', out_data.strip())
			PluginHelper.file_view_update(fl)
		except:
			import sys
			e = sys.exc_info()[1]
			print ' '.join(pargs)
			print e

	def id_is_open(self):
		return self.conf != None
	def id_is_ready(self):
		return self.conf.is_ready()
