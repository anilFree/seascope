#!/usr/bin/python

import os, sys, re
import subprocess
import shutil
import tempfile

GRAPH_ON_TYPES = ['function', 'macro']

def _eintr_retry_call(func, *args):
	while True:
		try:
			return func(*args)
		except OSError, e:
			if e.errno == errno.EINTR:
				continue
			raise

def ct_cmdForFile(f):
	#ct_args = 'ctags -n -u --fields=+K -f - --extra=+q'
	#ct_args = 'ctags -n -u --fields=+Ki -f -'
	ct_args = 'ctags -n -u --fields=+K -f -'
	if os.path.isdir(f):
		cmd = ct_args + ' -R'
		return cmd
	suffix_cmd_map = []
	custom_map = os.getenv('SEASCOPE_CTAGS_SUFFIX_CMD_MAP')
	if custom_map:
		custom_map = eval(custom_map)
		suffix_cmd_map += custom_map
	suffix_cmd_map.append( ['', ct_args] )
	for (suffix, cmd) in suffix_cmd_map:
		if f.endswith(suffix):
			return cmd
	return None

def ct_query(filename):
	args = ct_cmdForFile(filename)
	args = args.split()
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

class FFgraph:
	def __init__(self):
		self.cs_cmd_base = None

	def parse_cs_result(self, text):
		text = re.split('\r?\n', text)
		res = []
		for line in text:
			if line == '':
				continue
			line = line.split(' ', 3)
			line = [line[1], line[0], line[2], line[3]]
			res.append(line)
		return res

	def findCalleeList(self, caller, srcFile):
		try:
			cmd = self.cs_cmd_base + [ '-2', caller ]
			if os.path.isdir(srcFile):
				cmd = cmd + [ '-s' ]
			cmd = cmd + [ srcFile ] 
			# In python >= 2.7 can use subprocess.check_output
			# output = subprocess.check_output(cmd)
			proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
			(output, err_data) = proc.communicate()
			#print 'cmd =', cmd
			#print 'output =', output
			res = self.parse_cs_result(output)
			res = set([ e[0] for e in res ])
		except Exception as e:
			print >> sys.stderr, 'failed cmd:', cmd, ':', e
			res = []
		return res

	def generateDotHeader(self, name):
		out = 'digraph "%s" {\n' % name
		#out += '\tconcentrate=true;\n'
		return out

	def generateDotFooter(self):
		out = '}\n\n'
		return out
		
	def generateSubgraphHeader(self, name):
		out = '\tsubgraph "%s" {\n' % name
		return out

	def generateSubgraphFooter(self):
		out = '\t}\n\n'
		return out

	def generateClusterInfoLocal(self, localSym):
		out = ''
		# local
		out += self.generateSubgraphHeader('cluster_local_sym')
		for sym in localSym:
			out += '\t\t%s;\n' % sym
		out += self.generateSubgraphFooter()
		return out

	def generateClusterInfoExternal(self, externalSym):
		out = ''
		# extern
		out += self.generateSubgraphHeader('cluster_external_sym')
		for sym in externalSym:
			out += '\t\t%s;\n' % sym
		out += self.generateSubgraphFooter()
		return out

	def generateClusterInfo(self, localSym, externalSym):
		out = ''
		#out += self.generateClusterInfoLocal(localSym)
		out += self.generateClusterInfoExternal(externalSym)
		return out

	def generateDotInput(self, f, callerCalleInfo, is_extern):
		dotInput = ''
		dotInput += self.generateDotHeader(f)
		(localSym, externalSym, callerCalleInfo) = callerCalleInfo
		if is_extern:
			dotInput += self.generateClusterInfo(localSym, externalSym)
		# nodes
		for (caller, localCalleeList, externCalleeList) in callerCalleInfo:
			for callee in localCalleeList:
				dotInput += '\t"%s" -> "%s";\n' % (caller, callee)
			if not is_extern:
				continue
			for callee in externCalleeList:
				style = '[style=dotted]'
				dotInput += '\t"%s" -> "%s" %s;\n' % (caller, callee, style)
		dotInput += self.generateDotFooter()
		return dotInput

	def _generateDotGraph(self, f, is_extern, gOut):
		try:
			res = self.getCallerCalleeInfo(f, is_extern)
			dotInput = self.generateDotInput(f, res, is_extern)
		except Exception as e:
			print >> sys.stderr, e
		
		if not gOut:
			print dotInput
			return None

		args = ['dot', '-Tsvg']
		try:
			p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
			(svg_data, err_data) = p.communicate(dotInput)
			if err_data and err_data != '':
				print >> sys.stderr, err_data, '\n'
			#self.saveSvgFile(sym, svg_data)
			return svg_data
		except Exception as e:
			print >> sys.stderr, 'Failed to run:', ' '.join(args), '\n'
			print >> sys.stderr, 'dotInput:', dotInput, '\n'
			print >> sys.stderr, e, '\n'
		

	def generateDotGraph(self, f, is_extern, gOut):
		tmp_cs_dir = tempfile.mkdtemp(prefix='ffgraph_')
		if not tmp_cs_dir:
			print 'generateDotGraph: failed to create tmp dir'
			return
		self.cs_cmd_base = [ 'cscope', '-L', '-f', os.path.join(tmp_cs_dir, 'cscope.out') ]

		svg_data = None

		try:
			svg_data = self._generateDotGraph(f, is_extern, gOut)
		except:
			print 'generateDotGraph: failed'

		shutil.rmtree(tmp_cs_dir)
		
		return svg_data

	def getCallerCalleeInfo(self, f, is_extern):
		ct_out = ct_query(f)
		localSym = dict([ (e[0], e[2]) for e in ct_out ])
		lSym = []
		eSym = []
		res = []
		visitedCaller = dict()
		for e in ct_out:
			if e[2] in GRAPH_ON_TYPES:
				caller = e[0]
				if caller in visitedCaller:
					continue
				visitedCaller[caller] = True
				calleeList = self.findCalleeList(caller, f)
				localCalleeList = []
				externCalleeList = []
				for c in calleeList:
					if c in localSym and localSym[c] in GRAPH_ON_TYPES:
						localCalleeList.append(c)
						continue
					if is_extern:
						externCalleeList.append(c)
				res.append([caller, localCalleeList, externCalleeList])
				if is_extern:
					if len(localCalleeList) or len(externCalleeList):
						lSym += [caller] + localCalleeList
						eSym += externCalleeList
				else:
					if len(localCalleeList):
						lSym += [caller] + localCalleeList
		return [lSym, eSym, res]

def ff_graph(f, is_extern, gOut=True):
	#if not os.path.isfile(f):
		#return None
	ffg = FFgraph()
	#gOut = False
	svg_data = ffg.generateDotGraph(f, is_extern, gOut)
	return svg_data

if __name__ == '__main__':
	import optparse
	usage = "usage: %prog [options] (-d <code_dir/file> | -p <idutils_proj>) (-e) [symbol]"
	op = optparse.OptionParser(usage=usage)
	op.add_option("-e", action="store_true", dest="is_extern", help="include external sym")
	op.add_option("-d", "--codedir", dest="code_dir", help="Code dir", metavar="CODE_DIR")
	op.add_option("-p", "--project", dest="id_path", help="Idutils project dir", metavar="PROJECT")
	(options, args) = op.parse_args()

	if (not any([options.code_dir, options.id_path]) or
               all([options.code_dir, options.id_path])):
		print >> sys.stderr, 'Specify one among -d or -p'
		sys.exit(-1)

	sym = None
	dname = None
	is_extern = False
	if options.is_extern:
		is_extern = True
	if len(args):
		if len(args) != 1:
			print >> sys.stderr, 'Please specify only one symbol'
			sys.exit(-2)
		sym = args[0]

	svg_data = None
	if options.code_dir:
		dname = options.code_dir
		if not os.path.exists(dname):
			print >> sys.stderr, '"%s": does not exist' %  dname
			sys.exit(-3)
		svg_data = ff_graph(dname, is_extern=is_extern)
	print svg_data

