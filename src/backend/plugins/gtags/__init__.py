import os

def name():
	return 'gtags'

def is_your_prj(path):
	f = os.path.join(path, 'GTAGS')
	return os.path.exists(f)

def project_class():
	from GtagsProject import ProjectGtags
	return ProjectGtags
