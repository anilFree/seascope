# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os

def name():
	return 'generic_cmd'

def run_plugin(filename, parent, cmd=None):
	import GenericView
	GenericView.run(filename, parent, cmd=cmd)

def description():
	d = 'generic cmd description'
	return d

def cmd_name():
	import GenericView
	return GenericView.cmd_name()

priority = 100
