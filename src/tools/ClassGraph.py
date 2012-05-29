#!/usr/bin/env python

import sys
import subprocess
import os
import re

class ClassGraphGenerator:
	def __init__(self, d, wlimit=100):
		self.wdir = d;
		self.width_limit = wlimit;
		self.graphRules = []
		self.visitedRules = {}
		self.visitedSym = {}

	def addGraphRule(self, sym, d):
		if (sym, d) in self.visitedRules:
			return
		self.visitedRules[(sym, d)] = 1
		self.graphRules.append([sym, d])

	def refFiles(self, sym):
		args = ['lid', '-R', 'grep', sym]
		try:
			output = subprocess.check_output(args, cwd=self.wdir)
			output = re.split('\r?\n', output)
		except Exception as e:
			print >> sys.stderr, e
			print >> sys.stderr, 'Run this script from a directory where lid can find ID file'
			sys.exit(-1)
		res = set()
		for line in output:
			if line == '':
				continue
			f = line.split(':', 1)[0]
			f = os.path.normpath(os.path.join(self.wdir, f))
			res.add(f)
		return res

	def run_ctags(self, fl):
		cmd = 'ctags -n -u --fields=+i -L - -f -'
		args = cmd.split()
		proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		(out_data, err_data) = proc.communicate('\n'.join(fl))
		out_data = re.split('\r?\n', out_data)
		return out_data

	def derivedClasses(self, sym):
		fl = self.refFiles(sym)
		data = self.run_ctags(fl)

		res = []
		for line in data:
			if line == '':
				continue
			line = line.split('\t')
			if len(line) == 4:
				continue
			sd = dict([ x.split(':', 1) for x in line[4].split('\t')])
			if 'inherits' not in sd:
				continue
			sd = sd['inherits'].split(',')
			dd = [ re.split('::|\.', x.strip())[-1] for x in sd ]
			if sym in dd:
				res.append(line[0])
		return res

	def derivedClassesRecursive(self, symList):
		for sym in symList:
			if sym in self.visitedSym:
				return
			self.visitedSym[sym] = 1

			dclasses = self.derivedClasses(sym)
			if len(dclasses):
				if len(dclasses) > self.width_limit:
					print >> sys.stderr, 'num subclasses(%s) = %d, truncating to %d.' % (sym, len(dclasses), self.width_limit)
					dclasses = dclasses[0:self.width_limit]
					self.addGraphRule(sym, '"...(%s)"' % sym)
				for d in dclasses:
					self.addGraphRule(sym, d)
					self.derivedClassesRecursive(dclasses)

	def prepareDotInput(self, sym):
		if len(self.graphRules) == 0:
			print >> sys.stderr, 'No classes seem to inherit', sym
			sys.exit(-1)
		dotInput = 'digraph "%s" {\n' % sym
		for r in self.graphRules:
			dotInput += '\t"%s" -> "%s";\n' % (r[0], r[1])
		dotInput += '}\n'
		return dotInput

	def saveDotFile(self, sym, dotInput):
		f = open(sym + '.dot', 'w')
		f.write(dotInput)
		f.close()

	def saveImgFile(sym, svg_data):
		dot_svg = sym + '.svg'
		f = open(dot_svg, 'w')
		f.write(svg_data)
		f.close()

		print >> sys.stderr, 'saved', dot_svg

	def generateGraph(self, sym):
		self.derivedClassesRecursive([sym])
		dotInput = self.prepareDotInput(sym)
		# saveDotFile(sym, dotInput)

		args = ['dot', '-Tsvg']
		p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		(svg_data, err_data) = p.communicate(dotInput)
		if err_data and err_data != '':
			print >> sys.stderr, err_data

		#saveImgFile(sym, svg_data)
		return svg_data


if __name__ == '__main__':
	import optparse
	usage = "usage: %prog [options] symbol"
	op = optparse.OptionParser(usage=usage)
	op.add_option("-p", "--project", dest="id_path", help="Idutils project dir", metavar="PROJECT")
	op.add_option("-o", "--output", dest="output_path", help="Save image path", metavar="OUTPUT")
	(options, args) = op.parse_args()
	# id utils project dir
	if not options.id_path:
		print >> sys.stderr, 'idutils project path required'
		sys.exit(-1)
	id_path = os.path.normpath(options.id_path)
	if not os.path.exists(os.path.join(id_path, 'ID')):
		print >> sys.stderr, 'idutils project path does not exist'
		sys.exit(-2)
	# symbol
	if len(args) != 1:
		print >> sys.stderr, 'Please specify a symbol'
		sys.exit(-3)

	sym = args[0]
	#print options.id_path, args

	cgg = ClassGraphGenerator(id_path)
	svg_data = cgg.generateGraph(sym)
	print svg_data

