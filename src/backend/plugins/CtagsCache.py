from PyQt4.QtCore import *
from datetime import datetime
import re

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
		#res = out_data.strip().splitlines()
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
			self.sig.sig_result.emit(self.sig.sym, self.res)
	
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
			return
		if ct[m][1] != n:
			if ct[m][2] in ['variable']:
				#line[0] = '***** SMART *****'
				#print line
				return
			if f.endswith('.py'):
				while m > 0 and (ct[m][2] in ['namespace']):
					m = m - 1
				if m == - 1:
					return
		if ct[m][1] == n:
			if self.cmd_str == 'DEF':
				x = m
				y = m
				while x > 1 and ct[x - 1][1] == n:
					x = x - 1
				while y < len(ct) - 1 and ct[y + 1][1] == n:
					y = y + 1
				if x < y:
					for m in range(x, y + 1):
						if re.match(self.sig.sym, ct[m][0]):
							break
		line[0] = ct[m][0]

	def _run_ctags(self):
		cmd = 'ctags -n -u --fields=+K -L - -f -'
		args = cmd.split()
		import subprocess
		proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		(out_data, err_data) = proc.communicate('\n'.join(self.file_list))
		out_data = out_data.strip().splitlines()
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

		for line in self.res:
			if line[0] not in self.cond_list:
				continue
			self._ctags_fix(line)

		#t4 = datetime.now()
		#print '  fix', t4 - t3
		#print '  total', t4 - t2


ct_cache = {}

def flush():
	ct_cache = {}

