# -*- coding: utf-8 -*-
#
# boing/utils/matching.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import re

def matchKeys(first, second):
    """Return True if the key 'first' matches the key 'second'."""
    rvalue = False
    if first is not None and second is not None:
        if first==second: rvalue = True
        elif isinstance(first, str):
            if first.isidentifier():
                if isinstance(second, str) and not second.isidentifier():
                    rvalue = True if second==".*" else re.match("%s$"%second, first)
            elif first==".*":
                rvalue = True
            elif isinstance(second, int):
                rvalue = re.match("%s$"%first, str(second))
            elif isinstance(second, str) and second.isidentifier():
                rvalue = re.match("%s$"%first, second)
        elif isinstance(second, str) and not second.isidentifier():
            rvalue = True if second==".*" else re.match("%s$"%second, str(first))
    return rvalue

def matchPaths(first, second, start=0):
    """Return True if the path 'first' matches the path 'second'."""
    rvalue = False
    if first==second: rvalue = True
    elif isinstance(first, str) or isinstance(first, int):
        if isinstance(second, str) or isinstance(second, int):
            rvalue = matchKeys(first, second)
        elif isinstance(second, collections.Sequence) and second:
            rvalue = matchKeys(first, second[0])
    elif isinstance(first, collections.Sequence) and first:
        if isinstance(second, str) or isinstance(second, int):
            rvalue = matchKeys(first[0], second)
        elif isinstance(second, collections.Sequence) and second:
            if matchKeys(first[start], second[start]):
                next = start + 1                
                rvalue = True if next>=len(first) or next>=len(second) \
                    else matchPaths(first, second, next)
    return rvalue

def filterKeys(mapping, pattern):
    """Return an iterator over the keys of 'mapping' that match 'pattern'."""
    return mapping.keys() if pattern==".*" else _yieldKeys(mapping, pattern)

def _yieldKeys(mapping, pattern):
    if isinstance(pattern, str) and pattern.isidentifier() \
            or isinstance(pattern, int):
        if pattern in mapping: yield pattern
    elif isinstance(pattern, str): 
        regexp = re.compile(pattern)
        for key in mapping.keys():
            if isinstance(key, int): key = str(key)
            result = regexp.match(key)
            if result is not None and result.end()==len(key):
                yield key

def filterValues(mapping, pattern):
    """Return an iterator over the values of 'mapping', which keys
    match 'pattern'."""
    return mapping.values() if pattern==".*" else _yieldValues(mapping, pattern)

def _yieldValues(mapping, pattern):
    if isinstance(pattern, str) and pattern.isidentifier() \
            or isinstance(pattern, int):
        if pattern in mapping: yield mapping[pattern] 
    elif isinstance(pattern, str): 
        regexp = re.compile(pattern)
        for key, value in mapping.items():
            if isinstance(key, int): key = str(key)
            result = regexp.match(key)
            if result is not None and result.end()==len(key):
                yield value

def filterItems(mapping, pattern):
    """Return an iterator over the pairs (key, value) of 'mapping',
    which keys match 'pattern'."""
    return mapping.items() if pattern==".*" else _yieldItems(mapping, pattern)

def _yieldItems(mapping, pattern):
    if isinstance(pattern, str) and pattern.isidentifier() \
            or isinstance(pattern, int):
        if pattern in mapping: yield pattern, mapping[pattern] 
    elif isinstance(pattern, str): 
        regexp = re.compile(pattern)
        for key, value in mapping.items():
            if isinstance(key, int): key = str(key)
            result = regexp.match(key)
            if result is not None and result.end()==len(key):
                yield key, value

'''
def isConcrete(path, index=0):
    if index>=len(path): return True
    else:
        key = path[index]
        if isinstance(key, str) and key.isidentifier() \
                or isinstance(key, int):
            return isConcrete(path, index+1)
        else:
            return False
        
def concretize(pattern, reference, index=0):
    rvalue = None
    if index>=len(pattern): rvalue = list()        
    elif index>=len(reference):
        if isConcrete(pattern, index): rvalue = list(pattern)[index:]
    else:
        key = pattern[index]
        if isinstance(key, str) and key.isidentifier() \
                or isinstance(key, int):
            if key==reference[index]:
                rvalue = concretize(pattern, reference, index+1)
                if rvalue is not None: rvalue.insert(0, key)
            elif isConcrete(pattern, index+1):
                rvalue = list(pattern)[index:]
            else:
                rvalue = None
        elif isinstance(key, str) and matchKeys(key, reference[index]):
            rvalue = concretize(pattern, reference, index+1)
            if rvalue is not None: rvalue.insert(0, reference[index])
        else:
            rvalue = None
    return rvalue
        
def concretize(path, tree, index=0):
    rvalue = None
    key = path[index]
    if isinstance(key, str) and key.isidentifier() \
            or isinstance(key, int):
        if index==len(path)-1:
            rvalue = [[key]]
        elif key in tree:
            rvalue = concretize(path, tree[key], index+1)
            for inner in rvalue:
                inner.insert(0,key)
        else:
            rvalue = list()
    elif isinstance(key, str):
        rvalue = list()
        for concrete, subtree in tree.items(key):
            if index==len(path)-1:
                rvalue.append([concrete])
            else:
                subresult = concretize(path, subtree, index+1)
                for inner in subresult:
                    inner.insert(0, concrete)
                rvalue.extend(subresult)
    else:
        raise TypeError("path can only be composed by string or int, not %s"%
                        key.__class__.__name__)
    return rvalue
'''
        
            
