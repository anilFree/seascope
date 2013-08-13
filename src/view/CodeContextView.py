#!/usr/bin/env python

# Copyright (c) 2013 dangbinghoo <dangbinghoo@gmail.com>
# All rights reserved.
#
# License: BSD

import os
import re
import array

from PyQt4 import QtGui
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from EdView import EditorView

# code context view
class contextView(EditorView):
	sig_dbclick_contextview = pyqtSignal()
	def __init__(self, parent = None):
		EditorView.__init__(self, parent)
		
	def mouseReleaseEvent(self, ev):
		super(EditorView, self).mouseReleaseEvent(ev)
		
	def mousePressEvent(self, ev):
		pass
	
	def keyPressEvent(self, ev):
		pass
	
	def contextMenuEvent(self, ev):
		pass
	
	def	mouseDoubleClickEvent(self, ev):
		self.sig_dbclick_contextview.emit()

class codeResultView(QTextBrowser):
	sig_result_view_openfile = pyqtSignal(str, int)
	def __init__(self, parent = None):
		QTextBrowser.__init__(self)
		self.setReadOnly(True)
		
	def showResultList(self, sym, res):
		self.res = res
		richstr = '<div align="center">'
		richstr += '<span style="font-size:14px;color:#990000;">Query of &lt; <strong><span style="color:#000099;">'
		richstr += str(sym)
		richstr += '</span></strong></span> <span style="font-size:14px;color:#990000;"> &gt; list</span>'
		richstr += '<div align="left" style="line-height:2px">'
		richstr += '<hr />'
		for itm in res:
			filename = itm[1]
			linenum = itm[2]
			context = itm[3]
			richstr += 'Line <span style="font-size:12px;color:#6600CC;">'
			richstr += str(linenum)
			richstr += '</span> of <em><a href="'
			richstr += str(filename)
			richstr += '#'
			richstr += str(linenum)
			richstr += '">'
			richstr += str(filename)
			richstr += '</a>'
			richstr += '</span></span></em>'
			richstr += '<pre style="line-height:0px"><span style="font-size:12px;color:#006600;line-height:2px;">'
			richstr += str(context)
			richstr += '</span></pre>'
		richstr += '</div></div>'
		#print richstr
		self.setHtml(richstr)
		self.setReadOnly(True)
		self.anchorClicked.connect(self.anchorClicked_ev)
		
	def anchorClicked_ev(self, qurl):
		urlstr = qurl.toString()
		urlinfo = urlstr.split('#')
		fname = str(urlinfo[0])
		linen = int(urlinfo[1])
		self.sig_result_view_openfile.emit(fname, int(linen))
	
	def setSource(self, qurl):
		self.setText('')
		self.anchorClicked.disconnect(self.anchorClicked_ev)

# contextView Page
class CodeContextViewPage(QSplitter):
	def __init__(self, parent = None):
		QSplitter.__init__(self)
		self.setOrientation(Qt.Vertical)
		self.cv_filetitle = QLabel()
		self.cv = contextView()
		self.resv = codeResultView()
		self.addWidget(self.resv)
		self.addWidget(self.cv_filetitle)
		self.addWidget(self.cv)
		self.setSizes([1,1,1])
		self.resv.show()
		self.cv.hide()
		self.cv_filetitle.hide()
		self.cv_font = "Monospace,10,-1,5,75,0,0,0,0,0"

# ContextView Manager
class CodeContextViewManager(QTabWidget):
	sig_codecontext_showfile = pyqtSignal(str, int)
	def __init__(self, *args):
		apply(QTabWidget.__init__,(self, ) + args)
		self.setMovable(True)
		self.setTabsClosable(True)
		self.newContextViewPage()
		self.cvp_cv_openedFile = False
		
		self.cvp.cv.sig_dbclick_contextview.connect(self.contextViewPage_openfile)
		self.cvp.resv.sig_result_view_openfile.connect(self.resultViewPage_openfile)
	
	def newContextViewPage(self):
		self.cvp = CodeContextViewPage()
		self.addTab(self.cvp, 'Context View')

	def showResult(self, sym, res):
		# close last opened source file
		# FIXME: close file
		#if self.cvp_cv_openedFile:
		#	f =  self.cvp.cv.get_filename()
		#	close(f) 
		self.cvp.cv.clear()
			
		# if queried one, show the file, or, list results.
		if (len(res) == 1):
			self.cvp.resv.hide()
			self.cvp.cv.show()
			itm = res[0]
			self.cvp.filename = itm[1]
			self.cvp.linenum = itm[2]
			self.showFileContext(self.cvp.filename, self.cvp.linenum)
			self.cvp_cv_openedFile = True
		else:
			self.cvp.cv.hide()
			self.cvp.cv_filetitle.hide()
			self.cvp.resv.showResultList(sym, res)
			self.cvp.resv.show()
	
	def contextViewPage_openfile(self):
		self.cvp.cv.clear()
		self.sig_codecontext_showfile.emit(self.cvp.filename, int(self.cvp.linenum))
	
	def resultViewPage_openfile(self, filename, line):
		self.sig_codecontext_showfile.emit(filename, int(line))
			
	def showFileContext(self, fname, line):
		filetitle = '<span style="font-style:italic; color:#5500ff;">&nbsp;&nbsp;&nbsp;&nbsp;'
		filetitle += fname
		filetitle += '</span>'
		self.cvp.cv_filetitle.setText(filetitle)
		self.cvp.cv_filetitle.show()
		self.cvp.cv.open_file(fname)
		self.cvp.cv.set_font(self.cvp.cv_font)
		self.cvp.cv.goto_line(int(line))
		self.cvp.cv.setCaretLineBackgroundColor(QtGui.QColor("#ffaa7f"))
		self.cvp.cv.show_line_number_cb(True)
	
	def clear(self):
		self.cvp.cv_filetitle.clear()
		self.cvp.resv.clear()
		self.cvp.cv.clear()
		self.cvp.cv.hide()
