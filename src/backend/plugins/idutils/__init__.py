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
	d = 'GNU idutils supports various languages.\n'
	d += 'Seascope uses ctags to enhance the results.\n'
	d += '\nSupports ctags supported languages like C, C++, Python, Java etc\n'
	d += '\nJust make sure that idutils indexes the required files\n'
	return d

priority = 300
