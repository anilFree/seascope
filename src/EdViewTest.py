#!/usr/bin/python

if __name__ == '__main__':
	import sys, os, optparse
	
	usage = "usage: %prog filename"
	op = optparse.OptionParser(usage=usage)
	(options, args) = op.parse_args()

	if len(args) != 1:
		print >> sys.stderr, 'Please specify a filename'
		sys.exit(-1)
	filename = args[0]
	filename = os.path.abspath(filename)
	if not os.access(filename, os.R_OK):
		print 'Failed to read the file:', filename
		sys.exit(-2)


	app_dir = os.path.dirname(os.path.realpath(__file__))
	os.chdir(app_dir)

	from PyQt4 import QtGui, QtCore
	from PyQt4.QtGui import *
	from PyQt4.QtCore import *
	from view import EdView, EdViewRW
	import view
	
	view.load_plugins()

	app = QApplication(sys.argv)

	w = QMainWindow()
	if os.getenv("SEASCOPE_EDIT", 0):
		book = EdViewRW.EditorBookRW()
	else:
		book = EdView.EditorBook()

	actDescr = [
		[ book.find_cb,      'Ctrl+F' ],
                [ book.find_next_cb, 'F3' ],
                [ book.find_prev_cb, 'Shift+F3' ],
        ]
        for ad in actDescr:
		act = QAction(w)
		act.setShortcut(ad[1])
		act.triggered.connect(ad[0])
		w.addAction(act)

	w.setCentralWidget(book)
	w.resize(900, 600)
	w.show()

	book.show_file(filename)
	w.setWindowTitle(filename)

	sys.exit(app.exec_())
