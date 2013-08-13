# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import os

def name():
	return 'idutils'

def is_your_prj(path):
	f = os.path.join(path, 'ID')
	return os.path.exists(f)

def project_class():
	from IdutilsProject import ProjectIdutils
	return ProjectIdutils

def description():
	d = 'Preferred backend of seascope.\n'
	d += 'Some advanced features of seascope are available only with this backend\n'
	d += '\n'
	d += 'It\'s really "idutils + ctags" backend.\n'
	d += '    - idutils provides the indexing facility\n'
	d += '    - ctags provides the language intelligence\n'
	d += 'This backend combines both of these intelligently to provide superior source code browsing facility\n'
	d += '\n'
	d += 'A wide variety of languages are supported (ctags --list-languages)\n'
	d += 'For example C, C++, Java, Python etc\n'
	d += '\n'
	d += 'If your source files are not being indexed by idutils then configure it using /usr/share/id-lang.map\n'
	return d

priority = 800
