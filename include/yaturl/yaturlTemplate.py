#!/usr/bin/env python

def template(file, **vars):
    try:
        f = open(file, 'r')
        result = f.read() % vars
        f.close()
        return result
    except IOError:
        return ''
