# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os

def name():
	return 'ctags'

def run_plugin(filename, parent):
	import CtagsView
	CtagsView.run(filename, parent)

def description():
	d = 'ctags description'
	return d

priority = 500
