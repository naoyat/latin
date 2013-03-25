#!/usr/bin/env python
# -*- coding: utf-8 -*-

def dict_map(proc, d):
    return map(lambda k: proc(k, d[k]), d)

def tuple_map(proc, d):
    return map(lambda k: proc(*k), d)

def render(obj):
    klass = obj.__class__.__name__
    if klass == 'int':
        return str(obj)
    elif klass == 'str':
        return "'" + obj + "'"
    elif klass == 'unicode':
        return "'" + obj.encode('utf-8') + "'"
    elif klass == 'list':
        return '[' + ', '.join(map(render, obj)) + ']'
    elif klass == 'dict':
        return '{' + ', '.join(dict_map(render2, obj)) + '}'
    else:
        return '?'

def render2(k, v):
    return render(k) + ':' + render(v)

def pp(something):
    print render(something)
