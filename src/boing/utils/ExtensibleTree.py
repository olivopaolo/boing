# -*- coding: utf-8 -*-
#
# boing/utils/ExtensibleTree.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import copy as _copy
import itertools
import re

class tree_iterable(collections.Iterable, collections.Sized):

    def __init__(self, iterator):
        if not isinstance(iterator, collections.Iterator):
            if isinstance(iterator, collections.Iterable):
                iterator = iter(iterator)
            else:
                raise TypeError("argument must be iterator, not %s"%
                                iterator.__class__.__name__)
        self.__iter = iterator

    def __iter__(self):
        v, self.__iter = itertools.tee(self.__iter)
        return v

    def __len__(self):
        it = iter(self)
        if isinstance(it, collections.Sized): return len(it)
        else:
            i = 0
            for v in it:
                i += 1
            return i

    def __contains__(self, key):
        return key in list(self)


class tree_keys(tree_iterable):

    def __repr__(self):
        output = ", ".join(("%s"%i for i in self)) if self else ""
        return "tree_keys([%s])"%output


class tree_values(tree_iterable):

    def __getitem__(self, key):
        return tree_values(self._recursive_get(key))

    def __setitem__(self, key, value):
        for i in self:
            i[key] = value

    def _recursive_get(self, key):
        for i in self:
            item = i[key]
            if isinstance(item, tree_values):
                for r in item:
                    yield r
            else:
                yield item

    def __repr__(self):
        output = ", ".join(("%s"%i for i in self)) if self else ""
        return "tree_values([%s])"%output


class tree_items(tree_iterable):

    def __repr__(self):
        output = ", ".join(("(%s, %s)"%(k,v) for k,v in self)) if self else ""
        return "tree_items([%s])"%output


class ExtensibleTree(collections.MutableMapping):
    
    def __init__(self, flattentree=None):
        object.__setattr__(self, "_ExtensibleTree__info", dict())
        if flattentree is not None:
            for path, value in flattentree.items():
                self.set(path, value)

    def keys(self, pattern=slice(None)):
        """Return a new view of the tree’s keys, which match to pattern."""
        iterable = None
        if isinstance(pattern, slice):
            if pattern==slice(None): iterable = self.__info.keys()
            else: raise ValueError("slice %s not supported"%pattern)
        elif isinstance(pattern, str) and pattern.isidentifier() \
                or isinstance(pattern, int):
            iterable = (pattern, ) if pattern in self.__info else tuple()
        elif isinstance(pattern, str):
            iterable = (k for k in self.__info.keys() \
                            if re.match("%s$"%pattern, 
                                        k if isinstance(k, str) else str(k)))
        else: 
            raise TypeError("pattern must be string, integer or slice, not %s"%
                            pattern.__class__.__name__)
        return tree_keys(iterable)

    def values(self, pattern=slice(None)):
        """Return a new view of the tree’s branches, which match to pattern."""
        iterable = None
        if isinstance(pattern, slice):
            if pattern==slice(None): iterable = self.__info.values()
            else: raise ValueError("slice %s not supported"%pattern)
        elif isinstance(pattern, str) and pattern.isidentifier() \
                or isinstance(pattern, int):
            iterable = (self.__info[pattern], ) if pattern in self.__info \
                else tuple()
        elif isinstance(pattern, str):
            iterable = (v for k, v in self.__info.items() \
                            if re.match("%s$"%pattern, 
                                        k if isinstance(k, str) else str(k)))
        else: 
            raise TypeError("pattern must be string, integer or slice, not %s"%
                            pattern.__class__.__name__)
        return tree_values(iterable)

    def items(self, pattern=slice(None)):
        """Return a new view of the tree’s items ((key, value) pairs),
        which match to pattern."""
        iterable = None
        if isinstance(pattern, slice):
            if pattern==slice(None): iterable = self.__info.items()
            else: raise ValueError("slice %s not supported"%pattern)
        elif isinstance(pattern, str) and pattern.isidentifier() \
                or isinstance(pattern, int):
            iterable = ((pattern, self.__info[pattern]), ) \
                if pattern in self.__info else tuple()
        elif isinstance(pattern, str):
            iterable = ((k,v) for k, v in self.__info.items() \
                            if re.match("%s$"%pattern, 
                                        k if isinstance(k, str) else str(k)))
        else: 
            raise TypeError("pattern must be string, integer or slice, not %s"%
                            pattern.__class__.__name__)
        return tree_items(iterable)
    
    def paths(self, prefix=None, accumulate=None):
        """Return the set of all available paths."""
        if prefix is None: prefix = list()
        if accumulate is None: accumulate = set()
        if not self and prefix: accumulate.add(tuple(prefix))
        else:
            for key, value in self.items():
                prefix.append(key)
                if isinstance(value, ExtensibleTree):
                    accumulate = value.paths(prefix, accumulate)
                else:
                    accumulate.add(tuple(prefix))
                del prefix[-1]
        return accumulate

    def flatten(self, prefix=None, accumulate=None):
        """Return the tree as a flat dictionary with the tree's
        paths as keys, which map the respective leaf elements."""
        if prefix is None: prefix = list()
        if accumulate is None: accumulate = dict()
        if not self and prefix: accumulate[tuple(prefix)] = self
        else:
            for key, value in self.items():
                prefix.append(key)
                if isinstance(value, ExtensibleTree):
                    accumulate = value.flatten(prefix, accumulate)
                else:
                    accumulate[tuple(prefix)] = value
                del prefix[-1]
        return accumulate

    def match(self, path, index=0):
        """Return the matched subtree or None if 'path' does not
        matches."""
        rvalue = None
        if isinstance(path, str):
            if path.isidentifier():
                if path in self.__info:
                    value = self.__info[path]
                    rvalue = ExtensibleTree()
                    rvalue[path] = value if not isinstance(value, ExtensibleTree) \
                        else value.copy()
            else:
                matches = ExtensibleTree()
                for key, value in self.items(path):
                    matches[key] = value if not isinstance(value, ExtensibleTree) \
                        else value.copy()
                if matches: rvalue = matches 
        elif isinstance(path, int):
            if path in self.__info:
                value = self.__info[path]
                rvalue = ExtensibleTree()
                rvalue[path] = value if not isinstance(value, ExtensibleTree) \
                    else value.copy()
        elif isinstance(path, collections.Sequence):
            current = path[index]
            matches = ExtensibleTree()
            for key, value in self.items(current):
                if index==len(path)-1:
                    matches[key] = value if not isinstance(value, ExtensibleTree) \
                        else value.copy()
                elif isinstance(value, ExtensibleTree):
                    inner = value.match(path, index+1)
                    if inner is not None: matches[key] = inner
                else:
                    matches[key] = value
            if matches: rvalue = matches
        return rvalue

    def get(self, path, defvalue=None):
        """Return the value at path, or defvalue if it does not
        exist (no regexp)."""
        rvalue = defvalue
        if isinstance(path, str) or isinstance(path, int): 
            rvalue = self.__info.get(path, defvalue)
        elif isinstance(path, collections.Sequence):
            node = self
            for key in path:
                if not isinstance(node, ExtensibleTree): break
                node = node.get(key)
            else: 
                rvalue = node
        return rvalue
        
    def set(self, path, value):
        """Update the value at path (no regexp)."""
        if isinstance(path, str) or isinstance(path, int):
            self.__info[path] = value
        elif isinstance(path, collections.Sequence):
            node = self
            for key in path[:-1]:
                if not isinstance(node, ExtensibleTree):
                    raise ValueError("Invalid path: %s"%str(path))
                else: node = node[key]
            if isinstance(node, ExtensibleTree):
                node[path[-1]] = value
            else:
                raise ValueError("Invalid path: %s"%str(path))
        else: raise TypeError("Invalid path: %s"%str(path))

    def discard(self, path):
        """Remove the subtree at 'path' from the tree if it is present
        (no regexp)."""
        if isinstance(path, str) or isinstance(path, int):
            self.__info.pop(path, None)
        elif isinstance(path, collections.Sequence):
            node = self
            for key in path[:-1]:
                if not isinstance(node, ExtensibleTree): break
                node = node.get(key)
            else: 
                if isinstance(node, ExtensibleTree):
                    node.discard(path[-1])

    def update(self, other, reuse=False, getdiff=False):
        diff = ExtensibleTree() if getdiff else None
        for key, value in other.items():
            if key in self.__info:
                # Update case
                oldvalue = self.__info[key]
                if isinstance(value, ExtensibleTree):
                    if isinstance(oldvalue, ExtensibleTree):
                        inner = oldvalue.update(value, reuse, getdiff)
                        if getdiff: 
                            if "added" in inner: 
                                diff.added[key] = inner.added
                            if "updated" in inner: 
                                diff.updated[key] = inner.updated
                    else:
                        self[key] = value if reuse else value.copy()
                        if getdiff: diff.updated[key] = value.copy()
                elif oldvalue!=value:
                    if getdiff: diff.updated[key] = value
                    self[key] = value
            # Add case
            elif isinstance(value, ExtensibleTree):
                self[key] = value if reuse else value.copy()
                if getdiff: diff.added[key] = value.copy()
            else:
                self[key] = value
        return diff

    def remove_update(self, other, getdiff=False):
        """Remove all nodes for any path in 'other'. 'other's leaf
        values are not considered."""
        diff = ExtensibleTree() if getdiff else None
        for key, value in other.items():
            if key in self.__info:
                oldvalue = self.__info[key]
                if isinstance(value, ExtensibleTree):
                    if isinstance(oldvalue, ExtensibleTree):
                        inner = oldvalue.remove_update(value, getdiff)
                        if inner: diff.removed[key] = inner.removed
                    else: continue
                else:
                    del self.__info[key]
                    if getdiff: diff.removed[key] = None
        return diff

    # ---------------------------------------------------------------------
    #  Customizing attribute access

    def __getattr__(self, key):
        value = self.__info.get(key)
        if value is None:
            value = ExtensibleTree()
            self[key] = value
        return value

    def __setattr__(self, key, value):
        if key in self.__info:
            # update
            self.__info[key] = value
        elif key in dir(self.__class__) or key in self.__dict__:
            raise AttributeError(
                "'%s' object attribute '%s' is read-only"%(
                    self.__class__.__name__, key))
        else:
            # add
            self.__info[key] = value

    def __delattr__(self, key):
        if key in self.__class__.__dict__:
            raise AttributeError(
                "'%s' object attribute '%s' is read-only"%(
                    self.__class__.__name__, key))
        else:
            found = False
            try:
                del self.__info[key]
            except KeyError: pass
            else: found = True
            if not found: raise AttributeError(key)

    # ---------------------------------------------------------------------
    #  Basic customization
    def __repr__(self):
        output = ", ".join(("%s:%s"%(k,v) for k, v in self.items()))
        return "{%s}"%output

    # ---------------------------------------------------------------------
    #  Emulating container type

    def __len__(self):
        return len(self.__info)

    def __iter__(self):
        return iter(self.__info)

    def __getitem__(self, key):
        if isinstance(key, str) and key.isidentifier() or isinstance(key, int):
            value = self.__info.get(key)
            if value is None:
                value = ExtensibleTree()
                self[key] = value
            return value
        else:
            return self.values(key)
        
    def __setitem__(self, key, value):
        if isinstance(key, str) and key.isidentifier() or isinstance(key, int):
            error = None
            try:
                self.__setattr__(key, value)
            except AttributeError as err:
                error = str(err.args[0])
            if error is not None: raise KeyError(error)
        for k in self.keys(key):
            self.__info[k] = value

    def __delitem__(self, key):
        if isinstance(key, str) and key.isidentifier() or isinstance(key, int):
            found = False
            try:
                self.__delattr__(key)
            except AttributeError: pass
            else: found = True
            if not found: raise KeyError(key)
        else:
            i = 0
            for k in tuple(self.keys(key)):
                i += 1
                del self.__info[k]
            if not i: raise KeyError(key)

    def __contains__(self, path):
        """'path' can be a single string or integer or event the path
        to a tree node or leaf (no regexp)."""
        rvalue = False
        if isinstance(path, str) or isinstance(path, int): 
            rvalue = path in self.__info
        elif isinstance(path, collections.Sequence):
            node = self
            for key in path[:-1]:
                if not isinstance(node, ExtensibleTree): break
                node = node.get(key)
            else: 
                rvalue = isinstance(node, ExtensibleTree) and path[-1] in node
        return rvalue

    # ---------------------------------------------------------------------
    #  Copy methods

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        copy = ExtensibleTree()
        for key, value in self.items():
            if isinstance(value, ExtensibleTree): value = value.copy()
            copy[key] = value
        return copy

    def __deepcopy__(self, memo):
        copy = ExtensibleTree()
        for key, value in self.items():
            copy[key] = _copy.deepcopy(value, memo)
        return copy



if __name__=="__main__":    
    e = ExtensibleTree()
    e.a.a = 1
    e.b.c = []
    e.b.d = {}
    e.c = ExtensibleTree()
    print(e)
    ee = ExtensibleTree()
    ee.a.a = 2
    diff = ee.update(e, getdiff=True)
    print(ee)
    print(diff.flatten())

    
