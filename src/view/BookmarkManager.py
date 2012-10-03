#!/usr/bin/env python

# Copyright (c) 2012 Anthony Liu
# All rights reserved.
#
# License: BSD 

import sys
from array import *

class BookmarkManager():

	def __init__(self, parent=None):
		self.haystack = []
		
	def check(self, filename, line):
		if self.haystack.count((filename, line)):
			return 1
		return 0

	def append(self, filename, line):
		if self.check(filename, line) == 0:
			self.haystack.append((filename, line))
		return self.haystack.index((filename, line))
	
	def delete(self, filename, line):
		if self.haystack.count((filename, line)) == 0:
			return -1
		else:
			self.haystack.remove((filename, line))
			return 0
	
	def delete_index(self, index):
		if self.count() <= index:
			return -1
		elif index < 0:
			return -1
		else:
			self.haystack.pop(index)
			return 0
	
	def count(self):
		return len(self.haystack)
	
	def get(self, index):
		if self.count() <= index:
			return (None, None)
		elif index < 0:
			return (None, None)
		else:
			(filename, line) = self.haystack.pop(index)
			self.haystack.insert(index, (filename, line))
			return (filename, line)
		
	def clear(self):
		del self.haystack[:]

	def bookmarks(self):
		return self.haystack

	def dump(self):
		for i in range(len(self.haystack)):
			print >> sys.stderr, "bm index ", i, " ", self.haystack[i]

#############################################################################
#
# Basic unit test
#
#############################################################################

if __name__ == '__main__':
	
	bm = BookmarkManager()

	#
	# case 1, basic add, delete
	#
	
	print >> sys.stderr, "Initial empty"
	
	print >> sys.stderr, "bm has ", bm.count(), "items (0)"

	bm.append("file1", 100)
	bm.append("file2", 200)
	bm.append("file3", 300)

	print >> sys.stderr, "bm has " , bm.count(), "items (3) "
	
	bm.delete("file1", 100)

	print >> sys.stderr, "bm has " , bm.count(), "items (2)"
	
	bm.delete("file2", 100) # not existed

	print >> sys.stderr, "bm has " , bm.count(), "items (2)"

	bm.delete_index(1)

	print >> sys.stderr, "bm has " , bm.count(), "items (1)"

	#
	# case 2, dump
	#

	for i in range(bm.count()):
		(f, l) = bm.get(i)
		print >> sys.stderr, f, " (#", l, ")"

	#
	# case 3, duplicate
	#

	index = bm.append("file4", 400)
	print >> sys.stderr, "index for file4 #400 is " , index
	
	index = bm.append("file4", 400)
	print >> sys.stderr, "index for file4 #400 is " , index, " (again)"
	
	print >> sys.stderr, "bm has " , bm.count(), "items (2) "

	#
	# case 4, dump for eye examine
	#

	print >> sys.stderr, "bm dump for final check"

	bm.dump()
