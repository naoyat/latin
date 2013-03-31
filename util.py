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


def flatten_1(items):
    res = []
    for item in items:
        if isinstance(item, list):
            res += item
        else:
            res.append(item)
    return res

def variate(prefix, common_tags, suffices, suffices_tags):
    def aggregate(a_prefix, a_suffix, suffix_tags):
        return aggregate_dicts(common_tags, {'surface':a_prefix + a_suffix}, suffix_tags)

    def combine1(prefix, suffix, suffix_tags):
        if suffix is None:
            return []
        elif isinstance(suffix, tuple) or isinstance(suffix, list):
            return [aggregate(prefix, a_suffix, suffix_tags) for a_suffix in suffix]
        else:
            return aggregate(prefix, suffix, suffix_tags)

    def combine2(suffix, suffix_tags):
        return combine1(prefix, suffix, suffix_tags)

    if isinstance(prefix, tuple) or isinstance(prefix, list):
        items = map(combine1, prefix, suffices, suffices_tags)
    else:
        items = map(combine2,         suffices, suffices_tags)

    return flatten_1(items)
