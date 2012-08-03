# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os

def name():
	return 'cscope'

def is_your_prj(path):
	f = os.path.join(path, 'cscope.files')
	return os.path.exists(f)

def project_class():
	from CscopeProject import ProjectCscope
	return ProjectCscope

def description():
	d = 'Cscope supports C, lex, yacc files.\n'
	d += 'Support for C++ and Java is limited.'
	return d

priority = 500


