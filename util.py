#!/usr/bin/env python
# -*- coding: utf-8 -*-

def dict_map(proc, d):
    return map(lambda k: proc(k, d[k]), d)

def tuple_map(proc, d):
    return map(lambda k: proc(*k), d)

def aggregate_dicts(*dicts):
    dic = {}
    for d in dicts: dic.update(d)
    return dic

def render(obj):
    klass = obj.__class__.__name__
    if klass == 'int':
        return str(obj)
    elif klass == 'str':
        return "'" + obj + "'"
    elif klass == 'unicode':
        return "'" + obj.encode('utf-8') + "'"
    elif klass == 'list':
        return '[' + ',\n '.join(map(render, obj)) + ']'
    elif klass == 'dict':
        return '{' + ', '.join(dict_map(render2, obj)) + '}'
    else:
        return '?'

def render2(k, v):
    return render(k) + ':' + render(v)

def pp(something):
    print render(something)


#
# itemsの中で、criteriaに嵌らないアイテムだけ通すフィルタ
#
def remove_matched_items(items, criteria):
    # items = remove_matched_items(items, {'surface':u'mee'}) のような
    def p(item):
        for k, v in criteria.items():
            if item.has_key(k) and item[k] == v:
                return False
        return True
    return filter(p, items)
