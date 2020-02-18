#!/usr/bin/env python
# -*- coding: utf-8 -*-

def dict_map(proc, d):
    return [proc(k, d[k]) for k in d]

def tuple_map(proc, d):
    return [proc(*k) for k in d]

def aggregate_dicts(*dicts):
    dic = {}
    for d in dicts:
        # print d
        if len(d) > 0: dic.update(d)
    return dic

def render(obj, newline=False):
    klass = obj.__class__.__name__
    if klass == 'int':
        return str(obj)
    elif klass == 'str':
        return "'" + obj + "'"
    elif klass == 'unicode':
        return "'" + obj.encode('utf-8') + "'"
    elif klass == 'list':
        if newline:
            return '[' + ',\n '.join(map(render, obj)) + ']'
        else:
            return '[' + ', '.join(map(render, obj)) + ']'
    elif klass == 'tuple':
        return '(' + ', '.join(map(render, obj)) + ')'
    elif klass == 'dict':
        return '{' + ', '.join(dict_map(render2, obj)) + '}'
    else:
        return '?'

def render2(k, v):
    return render(k) + ':' + render(v)

def pp(something, newline=False):
    print(render(something, newline=newline))


#
# itemsの中で、criteriaに嵌らないアイテムだけ通すフィルタ
#
def remove_matched_items(items, criteria):
    # items = remove_matched_items(items, {'surface':u'mee'}) のような
    def p(item):
        for k, v in list(criteria.items()):
            if k in item and item[k] == v:
                return False
        return True
    return list(filter(p, items))


# 1階層だけ掘り下げる
def flatten_1(items):
    res = []
    for item in items:
        if isinstance(item, list) or isinstance(item, tuple):
            res += item
        else:
            res.append(item)
    return res


# 語尾変化
def variate(prefix, common_tags, suffices, suffices_tags):
    # def aggregate(a_prefix, a_suffix, suffix_tags):
    #    return aggregate_dicts(common_tags, {'surface':a_prefix + a_suffix}, suffix_tags)

    def combine1(prefix, suffix, suffix_tags):
        if suffix is None:
            return []
        elif isinstance(suffix, tuple) or isinstance(suffix, list):
            return [aggregate_dicts(common_tags, {'surface':prefix + a_suffix}, suffix_tags) for a_suffix in suffix]
            # return [aggregate(prefix, a_suffix, suffix_tags) for a_suffix in suffix]
        else:
            return aggregate_dicts(common_tags, {'surface':prefix + suffix}, suffix_tags)
            # return aggregate(prefix, suffix, suffix_tags)

    def combine2(suffix, suffix_tags):
        return combine1(prefix, suffix, suffix_tags)

    if isinstance(prefix, tuple) or isinstance(prefix, list):
        items = list(map(combine1, prefix, suffices, suffices_tags))
    else:
        items = list(map(combine2,         suffices, suffices_tags))

    return flatten_1(items)


# noun, pronoun, adj.
def aggregate_cases(items):
    tmp = {}

    for item in items:
        surface = item['surface']
        ja = item['ja']

        if 'gender' in item:
            cases_and_numbers = [(item['case'], item['number'], item['gender'])]
            del item['gender']
        else:
            cases_and_numbers = [(item['case'], item['number'])]
        del item['case']
        del item['number']

        if surface not in tmp:
            tmp[surface] = {}

        if ja in tmp[surface]:
            tmp[surface][ja]['_'] += cases_and_numbers
        else:
            item['_'] = cases_and_numbers
            tmp[surface][ja] = item

    result = []
    for surface,sub in list(tmp.items()):
        result += [items for ja,items in list(sub.items())]

    return result
