# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os
import sys
import re

backend_plugins = []
backend_dict = {}

def _load_plugins(module, directory):
	pluginImports = __import__(module, globals(), locals())
	print 'Scanning for backend plugins...'
	plist = []
	pdict = {}
	for i in sorted(os.listdir(directory)):
		path = os.path.join( directory, i, '__init__.py' )
		if os.path.isfile( path ):
			p = __import__( '%s.%s' % (module, i), globals(), locals(), ['*'] )
			plist.append(p)
			pdict[p.name()] = p
			if not hasattr(p, 'priority'):
				p.priority = 0 
	plist = sorted(plist, key=lambda p: p.priority, reverse=True)
	for p in plist:
		print '\t', p.name()
	return (plist, pdict)

def load_plugins():
	global backend_plugins, backend_dict
	(backend_plugins, backend_dict) = _load_plugins('backend.plugins', 'backend/plugins')

def plugin_list():
	return backend_plugins

def plugin_guess(proj_path):
	bi = []
	for p in backend_plugins:
		if p.is_your_prj(proj_path):
			bi.append(p.name())
	return bi


class BProject:
	def __init__(self):
		self.prj = None

	def proj_new_open_app_cb(self):
		self.prj.prj_feature_setup()

	def proj_close_app_cb(self):
		pass

	def _proj_new_open(self):
		self.proj_new_open_app_cb()

	def proj_new(self, bname, proj_args):
		b = backend_dict[bname]

		assert not self.prj
		prj = b.project_class().prj_new(proj_args)

		if prj:
			_proj_new_open()
		return self.prj != None

	def proj_open(self, proj_path, proj_type):
		b = backend_dict[proj_type]

		self.prj = b.project_class().prj_open(proj_path)

		if self.prj:
			self._proj_new_open()
		return self.prj != None

	def proj_close(self):
		self.prj.prj_close()
		self.prj = None
		
		from plugins import CtagsCache
		CtagsCache.flush()

		self.proj_close_app_cb()

	def proj_is_open(self):
		return self.prj != None

	def proj_name(self):
		return self.prj.prj_name() if self.prj else None

	def proj_dir(self):
		return self.prj.prj_dir() if self.prj else None

	def proj_src_files(self):
		return self.prj.prj_src_files()

	def proj_conf(self):
		return self.prj.prj_conf()

	def proj_settings_get(self):
		return self.prj.prj_settings_get()

	def proj_settings_update(proj_args):
		return self.prj.prj_settings_update(proj_args)

	def proj_is_ready(self):
		return self.prj.prj_is_ready()

	def proj_query(self, rquery):
		return self.prj.prj_query(rquery)

	def proj_rebuild(self):
		return self.prj.prj_rebuild()

	def proj_query_fl(self):
		return self.prj.prj_query_fl()

	def proj_type(self):
		return self.prj.prj_type()

	def proj_feature(self):
		return self.prj.prj_feature()
