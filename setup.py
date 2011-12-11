#!/usr/bin/env python

from distutils.core import setup

setup(name='Seascope',
	version='0.4a',
	description='A PyQt GUI front-end for cscope',
	long_description='A pyQt GUI front-end for cscope. Written in python using pyQt, QScintilla libraries.',
	url='http://seascope.googlecode.com',
	packages=['Seascope',
		'Seascope.backend',
		'Seascope.backend.plugins',
		'Seascope.backend.plugins.cscope',
		'Seascope.backend.plugins.gtags',
		'Seascope.view'
		],
	package_dir={'Seascope': 'src'},
	package_data={'Seascope': ['icons/*.svg','ui/*.ui']},
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
	options= {'bdist_rpm':{'requires': 'PyQt4,qscintilla-python,cscope,ctags',
				'group': 'Development Tools',
				'vendor': 'The Seascope Team'}}
	)
