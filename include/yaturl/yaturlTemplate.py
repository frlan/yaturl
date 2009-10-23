#!/usr/bin/env python

def template(file, **vars):
   	return open(file, 'r').read() % vars
