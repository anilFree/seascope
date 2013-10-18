#!/usr/bin/python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os, string, re
from PyQt4.QtCore import *

from ..PluginBase import ProjectBase, ConfigBase, QueryBase
import GtagsProjectUi
from GtagsProjectUi import QueryUiGtags

from .. import PluginHelper

class ConfigGtags(ConfigBase):
	def __init__(self):
		ConfigBase.__init__(self, 'gtags')

class ProjectGtags(ProjectBase):
	def __init__(self):
		ProjectBase.__init__(self)

	@staticmethod
	def _prj_new_or_open(conf):
		prj = ProjectGtags()
		prj.conf = conf
		prj.qry = QueryGtags(prj.conf)
		prj.qryui = QueryUiGtags(prj.qry)

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
			prj = ProjectGtags.prj_open(d)
			prj.qryui.do_rebuild()
			return prj
		return None

	@staticmethod
	def prj_open(proj_path):
		conf = ConfigGtags()
		conf.proj_open(proj_path)
		prj = ProjectGtags._prj_new_or_open(conf)
		return (prj)

	def prj_settings_trigger(self):
		proj_args = self.prj_conf()
		proj_args = QueryUiGtags.prj_show_settings_ui(proj_args)
		#if (proj_args == None):
			#return False
		#self.prj_update_conf(proj_args)
		#return True
		return False

from ..PluginBase import PluginProcess
from .. import PluginHelper
from ..CtagsCache import CtagsThread

class GtCtagsThread(CtagsThread):
	def __init__(self, sig):
		CtagsThread.__init__(self, sig)

	def ctags_bsearch(self, ct, n):
		m = CtagsThread.ctags_bsearch(self, ct, n)
		return m

	def parse_result(self, res, sig):
		res = self._filter_res(res, sig)
		return res

class GtProcess(PluginProcess):
	def __init__(self, wdir, rq):
		PluginProcess.__init__(self, wdir)
		self.name = 'gtags process'
		if rq == None:
			rq = ['', '']
		self.cmd_str = rq[0]
		self.req = rq[1]

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

		GtCtagsThread(sig).apply_fix(self.cmd_str, res, ['<unknown>'])

		return None

class QueryGtags(QueryBase):
	def __init__(self, conf):
		QueryBase.__init__(self)
		self.conf = conf

		self.gt_file_list_update()

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
		cmd_opt = GtagsProjectUi.cmd_str2id[cmd_str]
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
		qsig.connect(self.gt_file_list_update)
		return qsig

	def gt_file_list_update(self):
		wdir = self.conf.c_dir
		if not os.path.exists(os.path.join(wdir, 'GTAGS')):
			return
		fl = []
		try:
			import subprocess
			pargs = [ 'global', '-P', '-a' ]
			proc = subprocess.Popen(pargs, stdin=subprocess.PIPE, stdout=subprocess.PIPE, cwd=wdir)
			(out_data, err_data) = proc.communicate()
			fl = re.split('\r?\n', out_data.strip())
			PluginHelper.file_view_update(fl)
		except:
			import sys
			e = sys.exc_info()[1]
			print ' '.join(pargs)
			print e

	def gt_is_open(self):
		return self.conf != None
	def gt_is_ready(self):
		return self.conf.is_ready()
