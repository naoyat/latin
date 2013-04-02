#!/usr/bin/env python
# -*- coding: utf-8 -*-

def dict_map(proc, d):
    return map(lambda k: proc(k, d[k]), d)

def tuple_map(proc, d):
    return map(lambda k: proc(*k), d)

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
        items = map(combine1, prefix, suffices, suffices_tags)
    else:
        items = map(combine2,         suffices, suffices_tags)

    return flatten_1(items)


# noun, pronoun, adj.
def aggregate_cases(items):
    tmp = {}

    for item in items:
        surface = item['surface']
        ja = item['ja']

        if item.has_key('gender'):
            cases_and_numbers = [(item['case'], item['number'], item['gender'])]
            del item['gender']
        else:
            cases_and_numbers = [(item['case'], item['number'])]
        del item['case']
        del item['number']

        if not tmp.has_key(surface):
            tmp[surface] = {}

        if tmp[surface].has_key(ja):
            tmp[surface][ja]['_'] += cases_and_numbers
        else:
            item['_'] = cases_and_numbers
            tmp[surface][ja] = item

    result = []
    for surface,sub in tmp.items():
        result += [items for ja,items in sub.items()]

    return result
