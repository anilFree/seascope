# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os, re, subprocess
from datetime import datetime

from PyQt4.QtCore import QThread

#class CtagsInfo:
	#def __init__(self):
		#pass

	#@staticmethod
	#def lang_suffixes():
		#cmd = 'ctags --list-maps'
		#args = cmd.split()
		#import subprocess
		#proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		#(out_data, err_data) = proc.communicate()
		#res = re.split('\r?\n', out_data)
		# res = out_data
		#res = [ line.split(None, 1) for line in res if line != '' ]
		#d = {}
		#for line in res:
			#import fnmatch
			#fn_pats = line[1] .split()
			#print line[0], fn_pats
			#re_pats = '|'.join(fnmatch.translate(p) for p in fn_pats)
			#print line[0], re_pats
			#d[line[0]] = re_pats
		#print d
#print 'ctag.lang'
#CtagsInfo.lang_suffixes()

class CtagsThread(QThread):
	thread_list = []

	def __init__(self, sig):
		QThread.__init__(self)
		
		self.sig = sig
		self.ct_dict = {}
		
		self.finished.connect(self._finished_cb)
		CtagsThread.thread_list.append(self)
	
	def _finished_cb(self):
		#print 'CtagsThread.finished', len(self.ct_dict)
		CtagsThread.thread_list.remove(self)
		for k in self.ct_dict:
			ct_cache[k] = self.ct_dict[k]

		self.res = self.parse_result(self.res, self.sig)
		if self.res != None:
			self.sig.emit_result(self.res)
	
	def ctags_bsearch(self, ct, n):
		x = -1
		y = len(ct) - 1

		#print f, n
		while x < y:
			m = (x + y + 1) / 2
			#print '(', x, y, m, ')'
			if ct[m][1] > n:
				#print 'y: m -1', ct[m][1]
				m = m - 1
				y = m
				continue
			if ct[m][1] < n:
				#print 'x: m', ct[m][1]
				x = m
				continue
			break
		if y == -1:
			return y
		#assert x == m or y == m or ct[m][1] == n
		return m

	def _ctags_fix(self, line):
		f = line[1]
		n = int(line[2])
		ct = self.ct_dict[f]

		m = self.ctags_bsearch(ct, n)
		if m == -1:
			return True
		if ct[m][1] != n:
			if ct[m][2] in ['variable']:
				#line[0] = '***** SMART *****'
				#print line
				return True
			if f.endswith('.py'):
				while m > 0 and (ct[m][2] in ['namespace']):
					m = m - 1
				if m == - 1:
					return True
		if ct[m][1] == n:
			if self.cmd_str == 'DEF':
				x = m
				y = m
				while x > 1 and ct[x - 1][1] == n:
					x = x - 1
				while y < len(ct) - 1 and ct[y + 1][1] == n:
					y = y + 1
				if x > y:
					return False
				for m in range(x, y + 1):
					reqPat = self.sig.sym + '$'
					if re.match(reqPat, ct[m][0]):
						line[0] = ct[m][0]
						return True
					return False
		else:
			if self.cmd_str == 'DEF':
				return False
			if self.cmd_str == '-->':
				if f.endswith('.tac'):
					if ct[m][2] in ['reactor']:
						line[0] = ct[m][0].split('=>')[0].strip() + "Is"
						return True
		line[0] = ct[m][0]
		return True

	def runCtagsCustom(self, fl):
		custom_map = os.getenv('SEASCOPE_CTAGS_SUFFIX_CMD_MAP')
		if not custom_map:
			return []
		try:
			custom_map = eval(custom_map)
		except:
			print 'SEASCOPE_CTAGS_SUFFIX_CMD_MAP has errors'
			return []

		cmd_list = []
		for (suffix, cmd) in custom_map:
			_fl = [ f for f in fl if f.endswith(suffix) ]
			args = cmd.split()
			args += _fl
			cmd_list.append(args)

		if not len(cmd_list):
			return []

		out_data_all = []
		for args in cmd_list:
			proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			(out_data, err_data) = proc.communicate('\n'.join(fl))
			out_data = re.split('\r?\n', out_data)
			out_data_all += out_data
		return out_data_all

	def _run_ctags(self):
		cmd = 'ctags -n -u --fields=+K -L - -f -'
		args = cmd.split()
		proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		(out_data, err_data) = proc.communicate('\n'.join(self.file_list))
		out_data = re.split('\r?\n', out_data)
		out_data += self.runCtagsCustom(self.file_list)

		for line in out_data:
			if line == '':
				continue
			line = line.split('\t')
			f = line[1]
			num = line[2].split(';', 1)[0]
			line = [line[0], int(num), line[3]]
			self.ct_dict[f].append(line)

	def prepare_file_list(self):
		#t1 = datetime.now()
		flist = set()
		for line in self.res:
			if line[0] in self.cond_list:
				if line[1] not in ct_cache:
					flist.add(line[1])
				else:
					self.ct_dict[line[1]] = ct_cache[line[1]]
		for f in flist:
			self.ct_dict[f] = []

		#t2 = datetime.now()
		#print '  ', len(flist), 'flist', t2 - t1

		self.file_list = flist

	def apply_fix(self, cmd_str, res, cond_list):
		self.cmd_str = cmd_str
		self.res = res
		self.cond_list = cond_list

		self.prepare_file_list()
		self.start()

	def run(self):
		#t2 = datetime.now()

		self._run_ctags()
		
		#t3 = datetime.now()
		#print '  ct', t3 - t2
		res = []
		for line in self.res:
			if line[0] not in self.cond_list:
				continue
			if not self._ctags_fix(line):
				continue
			res.append(line)
		self.res = res
		#t4 = datetime.now()
		#print '  fix', t4 - t3
		#print '  total', t4 - t2

	def _filter_res(self, res, sig):
		req = sig.sym
		out_res = []
		if self.cmd_str == 'DEF':
			import_re = re.compile('^\s*import\s+')
			for line in res:
				reqPat = req + '$'
				if not re.match(reqPat, line[0]):
					continue
				if import_re.search(line[3]) and line[1].endswith('.py'):
					continue
				out_res.append(line)
			return out_res
		if self.cmd_str == '-->':
			call_re = re.compile('\\b%s\\b\s*\(' % req)
			extern_re = re.compile('^\s*extern\s+')
			reactor_re = re.compile('\\b(\w+::)*(\w+)\s*=>.*\\b%s\\b' % req)
			comment_re = re.compile('^\s*(\*\s|/\*|\*/|//\s|# )')
			func_ptr_re = re.compile('\\b(\w+)\s*(=|:)\s*%s\s*[,;:)]' % req)
			func_as_arg_re = re.compile('(^\s*|[(,]\s*)(\w+(\.|->))*%s\s*[,)]' % req);
			def _check_line():
				if line[1].endswith('.tac'):
					if '=>' in line[3]:
						grp = reactor_re.search(line[3])
						if grp:
							line[0] = grp.group(2) + "Is"
							return True
					# fallthru
				if line[0] == req:
					if not re.search('(\.|->)%s\\b' % req, line[3]):
						return False
					return True
				if call_re.search(line[3]):
					if extern_re.search(line[3]):
						return False
					return True
				grp = func_ptr_re.search(line[3])
				if grp:
					line[0] = grp.group(1)
					return True
				if not func_as_arg_re.search(line[3]):
					False
				return True
			for line in res:
				if not _check_line():
					continue
				if line[0] == '<unknown>':
					continue
				if comment_re.search(line[3]):
					continue
				out_res.append(line)
			return out_res
		if self.cmd_str == '<--':
			return res
		if self.cmd_str == 'INC':
			inc_re = re.compile('^\s*(#\s*include|(from\s+[^\s]+\s+)?import)\s+.*%s.*' % req)
			for line in res:
				if not inc_re.search(line[3]):
					continue
				out_res.append(line)
			return out_res
		return res

	def parse_result(self, res, sig):
		res = self._filter_res(res, sig)
		return res

ct_cache = {}

def flush():
	#print 'flushing ctags cache...'
	global ct_cache
	ct_cache = {}

