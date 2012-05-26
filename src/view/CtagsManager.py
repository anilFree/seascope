import subprocess

def _eintr_retry_call(func, *args):
	while True:
		try:
			return func(*args)
		except OSError, e:
			if e.errno == errno.EINTR:
				continue
			raise

def ct_query(filename):
	cmd = 'ctags -n -u --fields=+K -f -'
	args = cmd.split()
	args.append(filename)
	try:
		proc = subprocess.Popen(args, stdout=subprocess.PIPE)
		(out_data, err_data) = _eintr_retry_call(proc.communicate)
		out_data = out_data.split('\n')
	except Exception as e:
		out_data =  [
				'Failed to run ctags cmd\tignore\t0;\t ',
				'cmd: %s\tignore\t0;\t ' % ' '.join(args),
				'error: %s\tignore\t0;\t ' % str(e),
				'ctags not installed ?\tignore\t0;\t ',
			]
	res = []
	for line in out_data:
		if (line == ''):
			break
		line = line.split('\t')
		num = line[2].split(';', 1)[0]
		line = [line[0], num, line[3]]
		res.append(line)
	return res

import subprocess
import re
from collections import OrderedDict as xdict
#from collections import dict as xdict

class CtagsTreeBuilder:
	def __init__(self):
		#self.symTree = {}
		self.symTree = xdict({})

	def runCtags(self, f):
		#cmd = 'ctags -n -u --fields=+K -f - --extra=+q'
		#cmd = 'ctags -n -u --fields=+Ki -f -'
		cmd = 'ctags -n -u --fields=+K-f-t -f -'
		cmd = cmd.split()
		cmd.append(f)
		output = subprocess.check_output(cmd)
		return output

	def parseCtagsOutput(self, data):
		data = re.split('\r?\n', data)
		res = []
		for line in data:
			if line == '':
				continue
			line = line.split('\t', 4)
			res.append(line)
		return res


	def addToSymLayout(self, sc):
		t = self.symTree
		if sc and sc != '':
			for s in re.split('::|\.', sc):
				if s not in t:
					t[s] = xdict({})
					#t[s] = {}
				t = t[s]

	def addToSymTree(self, sc, line):
		t = self.symTree
		if sc and sc != '':
			for s in re.split('::|\.', sc):
				assert s in t
				t = t[s]

		cline = [line[0], line[2].split(';')[0], line[3]]
		if line[0] in t:
			#print line[0], 'in', t
			x = t[line[0]]
			if '+' not in x:
				x['+'] = cline
				return
		if '*' not in t:
			t['*'] = []
		t['*'].append(cline)
		#print '...', t, line

	def buildTree(self, data):
		# build layout using 5th field
		for line in data:
			if len(line) == 4:
				continue
			sd = dict([ x.split(':', 1) for x in line[4].split('\t')])
			line[4] = sd
			count = 0
			for t in [ 'namespace', 'class', 'struct', 'enum', 'function' ]:
				if t in sd:
					self.addToSymLayout(sd[t])
					count = count + 1
			if count != 1:
				print '******** count == 1 *********'
				print data
				print line
			#assert count == 1
		
		for line in data:
			if len(line) == 4:
				self.addToSymTree(None, line)
				continue
			sd = line[4]
			count = 0
			for t in [ 'namespace', 'class', 'struct', 'enum', 'function' ]:
				if t in sd:
					self.addToSymTree(sd[t], line)
					count = count + 1
			if count != 1:
				print '******** count == 1 *********'
				print data
				print line
			#assert count == 1

		return self.symTree

	def doQuery(self, filename):
		output = self.runCtags(filename)
		output = self.parseCtagsOutput(output)
		output = self.buildTree(output)
		return output


def ct_tree_query(filename):
	ct = CtagsTreeBuilder()
	output = ct.doQuery(filename)
	return output


