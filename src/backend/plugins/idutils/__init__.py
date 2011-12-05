import os

def name():
	return 'idutils'

def is_your_prj(path):
	f = os.path.join(path, 'ID')
	return os.path.exists(f)

def project_class():
	from IdutilsProject import ProjectIdutils
	return ProjectIdutils
