#!/usr/bin/env python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import sys
import subprocess
import os
import re

class ClassGraphGenerator:
	def __init__(self, d, wlimit=5000, is_base=False):
		self.wdir = d;
		self.width_limit = wlimit;
		self.graphRules = []
		self.visitedRules = {}
		self.visitedSym = {}
		if is_base:
			self.visitedSym = {'object' : 1}
			if os.getenv('SEASCOPE_CTAGS_SUFFIX_CMD_MAP'):
				for c in [ 'Entity', 'Type', 'PtrInterFace','Enum','Nominal' ]:
					self.visitedSym[c] = 1
					self.visitedSym['Tac::' + c] = 1
		self.is_base = is_base
		self.is_fq = False
		self.is_debug = os.getenv('SEASCOPE_CLASS_GRAPH_DEBUG')

	def addGraphRule(self, sym, d):
		if (sym, d) in self.visitedRules:
			return
		self.visitedRules[(sym, d)] = 1
		self.graphRules.append([sym, d])

	def refFiles(self, sym):
		args = ['lid', '-R', 'grep', sym]
		try:
			# In python >= 2.7 can use subprocess.check_output
			# output = subprocess.check_output(args, cwd=self.wdir)
			proc = subprocess.Popen(args, cwd=self.wdir, stdout=subprocess.PIPE)
			(output, err_data) = proc.communicate()
			output = re.split('\r?\n', output)
		except Exception as e:
			print >> sys.stderr, e, '\n'
			print >> sys.stderr, 'Run this script from a directory where lid can find ID file\n'
			sys.exit(-1)
		res = set()
		for line in output:
			if line == '':
				continue
			f = line.split(':', 1)[0]
			f = os.path.normpath(os.path.join(self.wdir, f))
			res.add(f)
		return res

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


	def runCtags(self, fl):
		cmd = 'ctags -n -u --fields=+i -L - -f -'
		args = cmd.split()
		proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		(out_data, err_data) = proc.communicate('\n'.join(fl))
		out_data = re.split('\r?\n', out_data)
		out_data += self.runCtagsCustom(fl)
		return out_data

	def parseCtagsInherits(self, sym, data):
		res = []
		for line in data:
			if line == '':
				continue
			line = line.split('\t', 4)
			if len(line) == 4:
				continue
			_sd = dict([ x.split(':', 1) for x in line[4].split('\t')])
			if 'inherits' not in _sd:
				continue
			sd = _sd['inherits'].strip()
			if sd == '':
				continue
			sd = sd.split(',')
			if self.is_fq:
				dd = [ x.strip() for x in sd ]
			else:
				dd = [ re.split('::|\.', x.strip())[-1] for x in sd ]
			try:
				if self.is_fq:
					cls_prefix = _sd['class']
				else:
					cls_prefix = None
			except:
				cls_prefix = None
			if not sym:
				res.append([line[0], dd])
				continue
			if self.is_base:
				if cls_prefix:
					if sym == cls_prefix + "::" + line[0]:
						res += dd
					if sym == cls_prefix + "." + line[0]:
						res += dd
				else:
					if sym == line[0]:
						res += dd
			else:
				if sym in dd:
					if cls_prefix:
						sep = '::'
						if '.' in cls_prefix:
							sep = '.'
						res.append(cls_prefix + sep + line[0])
					else:
						res.append(line[0])
		if self.is_debug:
			if sym:
				print sym, res
		return res

	def classHierarchy(self, sym):
		if self.is_fq:
			subSym = re.split('::|\.', sym)[-1]
		else:
			subSym = sym
		fl = self.refFiles(subSym)
		data = self.runCtags(fl)
		res = self.parseCtagsInherits(sym, data)
		return res

	def classHierarchyForDir(self, dname):
		fl = []
		for root, dirs, files in os.walk(dname, followlinks=True):
			fl += [os.path.join(root, f) for f in files]
		data = self.runCtags(fl)
		res = self.parseCtagsInherits(None, data)
		for (d, blist) in res:
			for b in blist:
				self.addGraphRule(b, d)
		return res

	def classHierarchyRecursive(self, symList):
		for sym in symList:
			if sym in self.visitedSym:
				continue
			self.visitedSym[sym] = 1

			dclasses = self.classHierarchy(sym)
			if len(dclasses):
				if len(dclasses) > self.width_limit:
					if is_base:
						s = 'base'
					else:
						s= 'derived'
					print >> sys.stderr, 'num %s classes(%s) = %d, truncating to %d.\n' % (s, sym, len(dclasses), self.width_limit)
					dclasses = dclasses[0:self.width_limit]
					self.addGraphRule(sym, '...(%s)' % sym)
				for d in dclasses:
					self.addGraphRule(sym, d)
				self.classHierarchyRecursive(dclasses)

	def prepareDotInput(self, sym=None, dname=None):
		if len(self.graphRules) == 0:
			if is_base:
				s = 'base'
			else:
				s= 'derived'
			print >> sys.stderr, 'No %s classes for %s\n' % (s, sym)
			sys.exit(0)
		if dname:
			name = dname
		else:
			name = sym
		dotInput = 'digraph "%s" {\n' % name
		if not dname:
			dotInput += '\t"%s" [style=bold];\n' % sym
		for r in self.graphRules:
			if not self.is_base:
				dotInput += '\t"%s" -> "%s";\n' % (r[0], r[1])
			else:
				dotInput += '\t"%s" -> "%s";\n' % (r[1], r[0])
		dotInput += '}\n'
		return dotInput

	def saveDotFile(self, sym, dotInput):
		f = open(sym + '.dot', 'w')
		f.write(dotInput)
		f.close()

	def saveSvgFile(sym, svg_data):
		dot_svg = sym + '.svg'
		f = open(dot_svg, 'w')
		f.write(svg_data)
		f.close()

		print >> sys.stderr, 'saved', dot_svg, '\n'

	def generateGraph(self, sym, dname=None):
		if sym:
			if sym == '::' or sym == '.':
				return
			if re.search('::|\.', sym):
				self.is_fq = True
			if sym.startswith('::') or sym.startswith('.'):
				sym = re.split('::|\.', sym, maxsplit=1)[-1]

			self.classHierarchyRecursive([sym])
			dotInput = self.prepareDotInput(sym=sym)
		else:
			if not dname:
				return
			self.classHierarchyForDir(dname)
			dotInput = self.prepareDotInput(dname=dname)

		if self.is_debug:
			print dotInput
			return ''
		#self.saveDotFile(sym, dotInput)

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
			print >> sys.stderr, e, '\n'


if __name__ == '__main__':
	import optparse
	usage = "usage: %prog [options] symbol"
	op = optparse.OptionParser(usage=usage)
	op.add_option("-p", "--project", dest="id_path", help="Idutils project dir", metavar="PROJECT")
	op.add_option("-b", action="store_true", dest="is_base", help="Show base classes")
	op.add_option("-d", "--codedir", dest="code_dir", help="Code dir", metavar="CODE_DIR")
	(options, args) = op.parse_args()
	# id utils project dir
	if not options.id_path:
		print >> sys.stderr, 'idutils project path required'
		sys.exit(-1)
	id_path = os.path.normpath(options.id_path)
	if not os.path.exists(os.path.join(id_path, 'ID')):
		print >> sys.stderr, 'idutils project path does not exist'
		sys.exit(-2)
	is_base = False
	if options.is_base:
		is_base = True
	if len(args) and options.code_dir:
		print >> sys.stderr, 'Cannot specify both -d and symbol'
		sys.exit(-3)
	if not len(args) and not options.code_dir:
		print >> sys.stderr, 'Specify one among -d and symbol'
		sys.exit(-4)

	cgg = ClassGraphGenerator(id_path, is_base=is_base)

	if options.code_dir:
		dname = options.code_dir
		svg_data = cgg.generateGraph(sym=None, dname=dname)
	else:
		if len(args) != 1:
			print >> sys.stderr, 'Please specify only one symbol'
			sys.exit(-5)
		sym = args[0]
		svg_data = cgg.generateGraph(sym)

	print svg_data
