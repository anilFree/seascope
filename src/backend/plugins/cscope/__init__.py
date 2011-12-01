import os

def name():
	return 'cscope'

def is_your_prj(path):
	f = os.path.join(path, 'cscope.files')
	return os.path.exists(f)

def project_class():
	from CscopeProject import ProjectCscope
	return ProjectCscope
