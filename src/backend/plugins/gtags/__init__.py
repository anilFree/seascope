import os

def name():
	return 'gtags+global'

def is_your_prj(path):
	f = os.path.join(path, 'GTAGS')
	return os.path.exists(f)
