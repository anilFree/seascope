# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os

def name():
	return 'gtags'

def is_your_prj(path):
	f = os.path.join(path, 'GTAGS')
	return os.path.exists(f)

def project_class():
	from GtagsProject import ProjectGtags
	return ProjectGtags

def description():
	d = 'GNU global/gtags supports C, C++, Yacc, Java, PHP and Assembly source files.\n'
	d += '\nSeascope uses ctags to enhance the results.'
	return d

#priority = 200
