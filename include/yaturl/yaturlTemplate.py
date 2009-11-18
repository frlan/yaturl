#!/usr/bin/env python

def template(file, **vars):
    f = open(file, 'r')
    result = f.read() % vars
    f.close()
    return result
