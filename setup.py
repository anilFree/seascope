#!/usr/bin/env python

from distutils.core import setup

setup(name='SeaScope',
	version='0.4a',
	description='A PyQt GUI front-end for cscope',
	long_description='A pyQt GUI front-end for cscope. Written in python using pyQt, QScintilla libraries.',
	url='http://seascope.googlecode.com',
	packages=['SeaScope',
		'SeaScope.backend',
		'SeaScope.backend.plugins',
		'SeaScope.backend.plugins.cscope',
		'SeaScope.backend.plugins.gtags',
		'SeaScope.view'
		],
	package_dir={'SeaScope': 'src'},
	package_data={'SeaScope': ['icons/*.svg','ui/*.ui']},
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
				'vendor': 'The SeaScope Team'}}
	)
