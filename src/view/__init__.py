__all__ = ["CallView", "ClassGraphView", "EdView", "FileView", "ResView"]

def load_plugins():
	import filecontext
	filecontext.load_plugins()