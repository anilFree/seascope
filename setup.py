#!/usr/bin/env python3

# Copyright (c) 2010 Anil Kumar
# All rights reserved.
#
# License: BSD 

import textwrap
from distutils.core import setup

setup(name='Seascope',
	version='0.9',
	description='A multi-platform multi-language source code browsing tool',
	long_description= textwrap.dedent("""A pyQt GUI front-end for idutils, cscope and gtags. Written in python using pyQt, QScintilla libraries."""),
	url='https://github.com/anilFree/seascope'
	packages=['Seascope',
		'Seascope.backend',
		'Seascope.backend.plugins',
		'Seascope.backend.plugins.idutils',
		'Seascope.backend.plugins.cscope',
		'Seascope.backend.plugins.gtags',
		'Seascope.view',
                'Seascope.view.filecontext',
                'Seascope.view.filecontext.plugins',
                'Seascope.view.filecontext.plugins.ctags_view',
                'Seascope.view.filecontext.plugins.generic_view',
		],
	package_dir={'Seascope': 'src'},
	package_data={'Seascope': ['icons/*.svg','tools/*.py', 'ui/*.ui', 'backend/plugins/*/ui/*.ui']},
	license="BSD License",
	classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: X11 Applications :: Qt',
          'Environment :: Win32 (MS Windows)',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: BSD License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Software Development',
          ],
	options= {'bdist_rpm':{'requires': 'PyQt5,python3-pyqt5.qsci,idutils,cscope,global,ctags,graphviz',
				'group': 'Development Tools',
				'vendor': 'The Seascope Team'}}
	)
