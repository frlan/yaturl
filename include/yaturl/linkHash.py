#!/usr/bin/env python

import hashlib

class linkHash:
	def __init__(self, hash=None, newlink=None):
		if hash is not None:
			self.hash = hash
		if newlink is not None:
			self.link = newlink
			self.hash = hashlib.sha1(newlink).hexdigest()
	
