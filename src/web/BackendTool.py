#!/usr/bin/env python

# Copyright (c) 2014 Anil Kumar
# All rights reserved.
#
# License: BSD

import os
import backend
import CtagsManager
from collections import OrderedDict

is_debug = os.getenv('SEASCOPE_WEB_DEBUG')

g_proj_d = OrderedDict()

def p_open(proj_path):
	bl = backend.plugin_guess(proj_path)
	if len(bl) == 0:
		msg = "Project '%s': No backend is interested" % proj_path
		print msg
		return None
	proj_type = bl[0]
	if len(bl) > 1:
		msg = "Project '%s': Many backends interested" % proj_path
		for b in be:
			msg += '\n\t' + b.name()
		msg += '\n\nGoing ahead with: ' + proj_type
		print msg
	print "Project '%s': using '%s' backend" % (proj_path, proj_type)

	bp = backend.BProject()
	rc = bp.proj_open(proj_path, proj_type)
	if rc:
		return bp
	else:
		return None

def find_prj(rd):
	pdir = rd.get('project', None)
	if not pdir:
		return None
	bp = g_proj_d.get(pdir, False)
	return bp

def p_query(bp, rquery):
	return bp.proj_query(rquery)

def p_query_fl(bp):
	return bp.proj_query_fl()

def validate_op(rd):
	for r in ['cmd_type', 'cmd_str', 'req']:
		if r not in rd:
			return False
	return True

def _run_op(rd):
	if is_debug:
		print 'rd', rd

	if not validate_op:
		return { 'err_data' : 'invalid request: validate_op failed' }

	cmd_type = rd['cmd_type']

	if cmd_type == 'project_list':
		res = g_proj_d.keys()
		outd = { 'res' : res }
		return outd
	if cmd_type == 'query':
		bp = find_prj(rd)
		if not bp:
			return { 'err_data' : 'failed to find project for query %s' % rd }

		if rd['cmd_str'] == 'FLIST':
			outd = p_query_fl(bp)
			res = []
			res.append(['file', 'path'])
			for r in outd['res']:
				res.append([os.path.basename(r), r])
			outd['res'] = res
			return outd
		if rd['cmd_str'] == 'FDATA':
			fname = rd['req']
			pdir = bp.proj_dir()
			if not fname.startswith(pdir):
				return { 'err_data' : 'file %s not in project %s' % (fname, pdir)}
			try:
				data = open(fname).read()
				outd = { 'res' : [ data ] }
				return outd
			except:
				return { 'err_data' : 'failed to read file %s' % fname }
		if rd['cmd_str'] == 'FCTAGS':
			fname = rd['req']
			if not fname.startswith(bp.proj_dir()):
				return []
			try:
				data = CtagsManager.ct_query(rd['req'])
				outd = { 'res' : [data] }
				return outd
			except:
				pass
		rquery = {
			'cmd' : rd['cmd_str'],
			'req' : rd['req'],
			'opt' : rd.get('opt', '').split(','),
			'hint_file' : rd.get('hint_file', ''),
		}
		outd = p_query(bp, rquery)
		if is_debug:
			print 'rquery', rquery
                return outd

	return { 'err_data' : 'invalid request: unknown cmd_type=%s' % cmd_type }

def run_op(rd):
	if is_debug:
		print '-' * 80
	outd = _run_op(rd)
	if is_debug:
		print '-' * 80

	if ('err_data' in outd) and outd['err_data']:
		print '==> ERR_DATA:', outd['err_data']
	res = outd.get('res', None)
	if not res and 'out_data' in outd:
		res = outd['out_data'].splitlines()
	#if not rd['cmd_str'] == 'FDATA':
		#for r in res:
			#print r
	if is_debug:
		print '-' * 80
	return outd

def load_projects(plist):
	backend.load_plugins()

	for p in plist:
		bp = p_open(p)
		if not bp:
			return False
		global g_proj_d
		pdir = bp.proj_dir()
		g_proj_d[pdir] = bp

	if not len(g_proj_d):
		print 'No projects'
		return False

	return True
