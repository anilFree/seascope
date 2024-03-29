# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import subprocess
import re, os

def _eintr_retry_call(func, *args):
	while True:
		try:
			return func(*args)
		except OSError as e:
			if e.errno == errno.EINTR:
				continue
			raise

def ct_override(filename):
	pattern = os.getenv('SEASCOPE_CTAGS_OVERRIDE_PATTERN')
	delim1  = os.getenv('SEASCOPE_CTAGS_OVERRIDE_DELIM_START')
	delim2  = os.getenv('SEASCOPE_CTAGS_OVERRIDE_DELIM_END')
	if not (pattern and delim1 and delim2):
		return

	args = ['grep', '-En', "%s" % pattern, "%s" % filename]
	try:
		proc = subprocess.Popen(args, stdout=subprocess.PIPE)
		(out_data, err_data) = _eintr_retry_call(proc.communicate)
		out_data = out_data.decode()
		out_data = out_data.split('\n')
	except Exception as e:
		out_data =  [
				'Failed to run ct override cmd\tignore\t0;\t ',
				'cmd: %s\tignore\t0;\t ' % ' '.join(args),
				'error: %s\tignore\t0;\t ' % str(e),
				'ctags not installed ?\tignore\t0;\t ',
			]
	res = {}
	for line in out_data:
		if (line == ''):
			break
		line = line.split(':', 1)
		num = line[0]
		inx1 = line[1].find(delim1) + 1
		inx2 = line[1].find(delim2)
		sym = line[1][inx1:inx2]
		res[num] = [sym, num, 'function']
	return res

def cmdForFile(f):
	#args = 'ctags -n -u --fields=+K -f - --extra=+q'
	#args = 'ctags -n -u --fields=+Ki -f -'
	args = 'ctags -n -u --fields=+K -f -'

	opt_I_file = os.getenv('SEASCOPE_CTAGS_OPT_I_FILE')
	if opt_I_file and os.path.isfile(opt_I_file):
		args += ' -I ' + opt_I_file

	suffix_cmd_map = []
	custom_map = os.getenv('SEASCOPE_CTAGS_SUFFIX_CMD_MAP')
	if custom_map:
		custom_map = eval(custom_map)
		suffix_cmd_map += custom_map
	suffix_cmd_map.append( ['', args] )
	for (suffix, cmd) in suffix_cmd_map:
		if f.endswith(suffix):
			return cmd
	return None

def ct_query(filename):
	override_res = ct_override(filename)

	args = cmdForFile(filename)
	args = args.split()
	args.append(filename)
	try:
		proc = subprocess.Popen(args, stdout=subprocess.PIPE)
		(out_data, err_data) = _eintr_retry_call(proc.communicate)
		out_data = out_data.decode()
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
		if override_res:
			override_ent = override_res.pop(num, None)
			if override_ent:
				line[0] = override_ent[0]
		line = [line[0], num, line[3]]
		res.append(line)
	if override_res:
		res += override_res.values()
		res = sorted(res, key=lambda e: int(e[1]))
	return res

is_OrderedDict_available = False
try:
	# OrderedDict available only in python >= 2.7
	from collections import OrderedDict
	is_OrderedDict_available = True
except:
	pass

def emptyOrderedDict():
	if is_OrderedDict_available:
		return OrderedDict({})
	return {}

class CtagsTreeBuilder:
	def __init__(self):
		self.symTree = emptyOrderedDict()

	def cmdForFile(self, f):
		#args = 'ctags -n -u --fields=+K -f - --extra=+q'
		#args = 'ctags -n -u --fields=+Ki -f -'
		args = 'ctags -n -u --fields=+K-f-t -f -'

		opt_I_file = os.getenv('SEASCOPE_CTAGS_OPT_I_FILE')
		if opt_I_file and os.path.isfile(opt_I_file):
			args += ' -I ' + opt_I_file

		suffix_cmd_map = []
		custom_map = os.getenv('SEASCOPE_CTAGS_SUFFIX_CMD_MAP')
		if custom_map:
			custom_map = eval(custom_map)
			suffix_cmd_map += custom_map
		suffix_cmd_map.append( ['', args] )
		for (suffix, cmd) in suffix_cmd_map:
			if f.endswith(suffix):
				return cmd
		return None

	def runCtags(self, f):
		args = self.cmdForFile(f)
		args = args.split()
		args.append(f)
		# In python >= 2.7 can use subprocess.check_output
		# output = subprocess.check_output(args)
		# return output
		proc = subprocess.Popen(args, stdout=subprocess.PIPE)
		(out_data, err_data) = proc.communicate()
		out_data = out_data.decode()
		return out_data

	def parseCtagsOutput(self, data, override_res, filename):
		data = re.split('\r?\n', data)
		res = []
		for line in data:
			if line == '':
				continue
			try:
				line = line.split('\t', 4)
				if override_res:
					num = line[2].split(';', 1)[0]
					override_ent = override_res.pop(num, None)
					if override_ent:
						line[0] = override_ent[0]
				res.append(line)
			except:
				print('bad line:', line)
		if override_res:
			for line in override_res.values():
				line = [line[0], filename, line[1], line[2]]
				res.append(line)
			res = sorted(res, key=lambda e: int(e[2].split(';')[0]))
		return res


	def addToSymLayout(self, sc):
		t = self.symTree
		if sc and sc != '':
			for s in re.split('::|\.', sc):
				if s not in t:
					t[s] = emptyOrderedDict()
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
		type_list = [ 'namespace', 'class', 'interface', 'struct', 'union', 'enum', 'function' ]
		# build layout using 5th field
		for line in data:
			if len(line) == 4:
				continue
			try:
				sd = dict([ x.split(':', 1) for x in line[4].split('\t')])
			except:
				print('bad line', line)
				continue
			line[4] = sd
			count = 0
			for t in type_list:
				if t in sd:
					self.addToSymLayout(sd[t])
					count = count + 1
			if count != 1:
				print('******** count == 1 *********')
				print(data)
				print(line)
			#assert count == 1
		
		if len(self.symTree) == 0:
			return (data, False)
		
		for line in data:
			if len(line) == 4:
				self.addToSymTree(None, line)
				continue
			sd = line[4]
			count = 0
			for t in type_list:
				if t in sd:
					self.addToSymTree(sd[t], line)
					count = count + 1
			if count != 1:
				print('******** count == 1 *********')
				print(data)
				print(line)
			#assert count == 1

		return (self.symTree, True)

	def doQuery(self, filename):
		try:
			output = self.runCtags(filename)
			override_res = ct_override(filename)
			output = self.parseCtagsOutput(output, override_res, filename)
			output = self.buildTree(output)
		except Exception as e:
			print(str(e))
			output = [None, False]
		return output


def ct_tree_query(filename):
	ct = CtagsTreeBuilder()
	output = ct.doQuery(filename)
	return output

if __name__ == '__main__':
	import optparse
	import sys
	depth = 0
	def recursePrint(t):
		global depth
		for k, v in list(t.items()):
			if k == '*':
				for line in v:
					print('%s%s' % (' ' * depth, line))
				continue
			if k == '+':
				continue

			if '+' in v:
				k = v['+']
			print('%s%s' % (' ' * depth, k))
				
			depth = depth + 4
			recursePrint(v)
			depth = depth - 4

	op = optparse.OptionParser()
	(options, args) = op.parse_args()
	if len(args) != 1:
		print('Please specify a file')
		sys.exit(-1)

	(output, isTree) = ct_tree_query(args[0])
	if isTree:
		recursePrint(output)
	else:
		for line in output:
			print(line)

