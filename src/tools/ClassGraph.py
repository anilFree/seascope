#!/usr/bin/env python

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
		self.is_base = is_base

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

	def runCtags(self, fl):
		cmd = 'ctags -n -u --fields=+i -L - -f -'
		args = cmd.split()
		proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		(out_data, err_data) = proc.communicate('\n'.join(fl))
		out_data = re.split('\r?\n', out_data)
		return out_data

	def classHierarchy(self, sym):
		fl = self.refFiles(sym)
		data = self.runCtags(fl)

		res = []
		for line in data:
			if line == '':
				continue
			line = line.split('\t', 4)
			if len(line) == 4:
				continue
			sd = dict([ x.split(':', 1) for x in line[4].split('\t')])
			if 'inherits' not in sd:
				continue
			sd = sd['inherits']
			if sd == '':
				continue
			sd = sd.split(',')
			dd = [ re.split('::|\.', x.strip())[-1] for x in sd ]
			if self.is_base:
				if sym == line[0]:
					res += dd
			else:
				if sym in dd:
					res.append(line[0])
		return res

	def classHierarchyRecursive(self, symList):
		for sym in symList:
			if sym in self.visitedSym:
				return
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

	def prepareDotInput(self, sym):
		if len(self.graphRules) == 0:
			if is_base:
				s = 'base'
			else:
				s= 'derived'
			print >> sys.stderr, 'No %s classes for %s\n' % (s, sym)
			sys.exit(0)
		dotInput = 'digraph "%s" {\n' % sym
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

	def generateGraph(self, sym):
		self.classHierarchyRecursive([sym])
		dotInput = self.prepareDotInput(sym)
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
	# symbol
	if len(args) != 1:
		print >> sys.stderr, 'Please specify a symbol'
		sys.exit(-3)

	sym = args[0]
	#print options.id_path, args

	cgg = ClassGraphGenerator(id_path, is_base=is_base)
	svg_data = cgg.generateGraph(sym)
	print svg_data
