#!/usr/bin/env python

# Copyright (c) 2014 Anil Kumar
# All rights reserved.
#
# License: BSD

import sys
import os
import subprocess
import threading

class PluginProcess:
	def __init__(self, pargs):
		self.pargs = pargs
		self.proc = None
		self.res = {
				'out_data' : None,
				'err_data' : None,
			}

	def run(self):
		try:
			self.proc = subprocess.Popen(self.pargs, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			(out_data, err_data) = self.proc.communicate()
			self.res['out_data'] = out_data
			self.res['err_data'] = err_data
		except Exception as e:
			print 'PluginProcess.run():', e
			self.res['err_data'] = str(e)
		return self.res
