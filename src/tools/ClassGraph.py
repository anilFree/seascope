#!/usr/bin/env python

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import sys
import subprocess
import os
import re

class CtagsInhCache:
	def __init__(self, is_base, is_fq, is_debug):
		self.cit_cache = {}
		self.is_base   = is_base
		self.is_fq     = is_fq
		self.is_debug  = False

		map = os.getenv('SEASCOPE_CTAGS_SUFFIX_CMD_MAP', 0)
		if map:
			try:
				map = eval(map)
			except:
				print 'SEASCOPE_CTAGS_SUFFIX_CMD_MAP has errors'
				map = None
		self.ct_custom_map = map

	def _filterCtInherits(self, data, sym=None):
		res = {}
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
			if 'class' in _sd:
				cls = _sd['class'].strip()
			else:
				cls = None
			if line[1] not in res:
				res[line[1]] = []
			res[line[1]].append([line[0], sd, cls])
			if self.is_debug:
				print line[0], line[1], sd, cls
		return res

	def _runCtagsCustom(self, fl):
		if not self.ct_custom_map:
			return []
		cmd_list = []
		for (suffix, cmd) in self.ct_custom_map:
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

	def _runCtags(self, fl):
		cmd = 'ctags -n -u --fields=+i -L - -f -'
		args = cmd.split()
		proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
		(out_data, err_data) = proc.communicate('\n'.join(fl))
		out_data = re.split('\r?\n', out_data)
		out_data += self._runCtagsCustom(fl)
		return out_data

	def runCtagsInh(self, fl):
		data = self._runCtags(fl)
		ct_dict = self._filterCtInherits(data, None)
		for f in fl:
			if f not in ct_dict:
				ct_dict[f] = []
		return ct_dict

	def ctInhInfo(self, flist):
		fl = [ f for f in flist if f not in self.cit_cache ]
		#print len(fl), len(flist), len(self.cit_cache)
		if len(fl):
			ct_dict = self.runCtagsInh(fl)
			self.cit_cache.update(ct_dict)
		res = []
		for f in flist:
			res += self.cit_cache[f]
		return res

class ClassGraphGenerator:
	def __init__(self, d, pcmd=None, wlimit=5000, is_base=False):
		self.wdir = d;
		self.pcmd = pcmd
		self.width_limit = wlimit;
		self.dname = None
		self.dirCtInhInfo = None
		self.graphRules = []
		self.visitedRules = {}
		self.visitedSym = {}
		if is_base:
			self.visitedSym = {'object' : 1}
			if os.getenv('SEASCOPE_CTAGS_SUFFIX_CMD_MAP', 0):
				for c in [ 'Entity', 'Type', 'PtrInterFace','Enum','Nominal' ]:
					self.visitedSym[c] = 1
					self.visitedSym['Tac::' + c] = 1
		self.is_base = is_base
		self.is_fq = False
		self.is_debug = os.getenv('SEASCOPE_CLASS_GRAPH_DEBUG', 0)
		self.cic = CtagsInhCache(self.is_base, self.is_fq, self.is_debug)

	def addGraphRule(self, sym, d):
		if (sym, d) in self.visitedRules:
			return
		self.visitedRules[(sym, d)] = True
		self.graphRules.append([sym, d])

	def refFiles(self, sym):
		args = list(self.pcmd) + [sym]
		try:
			# In python >= 2.7 can use subprocess.check_output
			# output = subprocess.check_output(args, cwd=self.wdir)
			proc = subprocess.Popen(args, cwd=self.wdir, stdout=subprocess.PIPE)
			(output, err_data) = proc.communicate()
			output = re.split('\r?\n', output)
		except Exception as e:
			print >> sys.stderr, 'dir:', self.wdir, ':cmd:', args, ':', e, '\n'
			sys.exit(-1)
		res = set()
		for line in output:
			if line == '':
				continue
			f = line.split(':', 1)[0]
			f = os.path.normpath(os.path.join(self.wdir, f))
			res.add(f)
		return res

	def parseCtagsInherits(self, data, sym=None):
		res = []
		for line in data:
			sd = line[1]
			if sd == '':
				continue
			sd = sd.split(',')
			if self.is_fq:
				dd = [ x.strip() for x in sd ]
				cls = line[2]
			else:
				dd = [ re.split('::|\.', x.strip())[-1] for x in sd ]
				cls = None
			if not sym:
				res.append([line[0], dd])
				continue
			if self.is_base:
				if cls:
					if sym == cls + "::" + line[0]:
						res += dd
					if sym == cls + "." + line[0]:
						res += dd
				else:
					if sym == line[0]:
						res += dd
			else:
				if sym in dd:
					if cls:
						sep = '::'
						if '.' in cls:
							sep = '.'
						res.append(cls + sep + line[0])
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

		if self.pcmd:
			fl = self.refFiles(subSym)
			data = self.cic.ctInhInfo(fl)
		else:
			data = self.dirCtInhInfo

		res = self.parseCtagsInherits(data, sym)
		return res

	def runCtInhForDir(self, dname):
		self.dname = dname
		fl = []
		for root, dirs, files in os.walk(dname, followlinks=True):
			fl += [os.path.join(root, f) for f in files]
		self.dirCtInhInfo = self.cic.ctInhInfo(fl)

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

	def classHierarchyForDir(self, dname):
		res = self.parseCtagsInherits(self.dirCtInhInfo)
		for (d, blist) in res:
			for b in blist:
				self.addGraphRule(b, d)

	def prepareDotInput(self, sym_or_dname):
		if len(self.graphRules) == 0:
			if is_base:
				s = 'base'
			else:
				s= 'derived'
			print >> sys.stderr, 'No %s classes for %s\n' % (s, sym_or_dname)
			sys.exit(0)
		dotInput = 'digraph "%s" {\n' % sym_or_dname
		if not sym_or_dname:
			dotInput += '\t"%s" [style=bold];\n' % sym_or_dname
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

	def generateGraph(self, dname, sym=None):
		if not self.pcmd:
			self.runCtInhForDir(dname)
		if sym:
			if sym == '::' or sym == '.':
				return
			if re.search('::|\.', sym):
				self.is_fq = True
			if sym.startswith('::') or sym.startswith('.'):
				sym = re.split('::|\.', sym, maxsplit=1)[-1]
			self.classHierarchyRecursive([sym])
			dotInput = self.prepareDotInput(sym)
		else:
			self.classHierarchyForDir(dname)
			dotInput = self.prepareDotInput(dname)

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
	usage = "usage: %prog [options] (-d <code_dir/file> | -t <prj_type>) [symbol]"
	op = optparse.OptionParser(usage=usage)
	op.add_option("-b", action="store_true", dest="is_base", help="Show base classes")
	op.add_option("-d", "--codedir", dest="code_dir", help="Code dir", metavar="CODE_DIR")
	op.add_option("-t", "--type", dest="prj_type", help="project type: idutils|gtags|cscope", metavar="PRJ_TYPE")
	(options, args) = op.parse_args()

	# dname
	if not options.code_dir:
		print >> sys.stderr, 'Specify -d'
		sys.exit(-1)
	dname = options.code_dir
	if not os.path.exists(dname):
		print >> sys.stderr, '"%s": does not exist' %  dname
		sys.exit(-2)
	wdir = dname
	if not os.path.isdir(wdir):
		wdir = os.path.dirname(wdir)

	# sym
	sym = None
	if len(args):
		if len(args) != 1:
			print >> sys.stderr, 'Please specify only one symbol'
			sys.exit(-3)
		sym = args[0]

	# ptype
	ptype = options.prj_type
	if ptype:
		if not sym:
			print >> sys.stderr, '-t option needs sepficfying symbol'
			sys.exit(-4)
		if not os.path.isdir(dname):
			print >> sys.stderr, '-t option needs codedir to be a directory'
			sys.exit(-5)
	pcmd = None
	if ptype and os.path.isdir(dname):
		prj_list = [
			['idutils', 'ID',        ['lid', '-R', 'grep', '--']                          ],
			['gtags', 'GRTAGS',      ['global', '-a', '--result=grep', '-x', '-r', '--']  ],
			['cscope', 'cscope.out', ['cscope', '-L', '-d',  '-0', '--']                  ],
			['grep',   '',           ['grep', '-R', '-n', '-I', '--',]                    ],
		]
		for p in prj_list:
			if p[0] == ptype:
				if os.path.exists(os.path.join(dname, p[1])):
					pcmd = p[2]
				break
	# is_base
	is_base = options.is_base

	# run
	cgg = ClassGraphGenerator(wdir, pcmd=pcmd, is_base=is_base)
	svg_data = cgg.generateGraph(dname, sym)

	print svg_data
