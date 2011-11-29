# -*- coding: utf-8 -*-
#
# boing/utils/ExtensibleTree.py -
#
# Authors: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
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


class NonRecursiveNode(collections.MutableMapping):
    
    def __init__(self, flattentree=None):
        object.__setattr__(self, "_NonRecursiveNode__info", dict())
        if isinstance(flattentree, collections.Mapping):
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
            print("pattern", pattern)
            print()
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

    def set(self, path, value):
        """Set to value the tree node which is pointed by path."""
        if isinstance(path, str) or isinstance(path, int): path = (path, )
        if path:
            first, *rest = path
            if not rest: 
                self[first] = value
            else: 
                self[first].set(rest, value)

    def match(self, path, forced=False):
        """Return the matched subtree or None if 'path' does not
        matches. 'path' must fully match in order to be accepted. If
        'forced' is True, recursion is forced to NonRecursiveNode
        also."""
        if isinstance(path, str) or isinstance(path, int): path = (path, )
        if path:
            first, *rest = path
            matches = self.items(first)
            if matches:
                subtree = type(self)()
                for key, value in matches:
                    if not rest:
                        subtree[key] = value
                    elif isinstance(value, ExtensibleTree) \
                            or isinstance(value, NonRecursiveNode) and forced:
                        inner = value.match(rest, forced)
                        if inner is not None: subtree[key] = inner
                if not subtree: subtree = None
                return subtree
        return None

    def update(self, other, getdiff=False):
        """Update the tree with the ('path','value') pairs from
        'other'. If 'getdiff' is True the diff tree is returned,
        otherwise None is returned."""
        if not isinstance(other, collections.Mapping):
            raise TypeError("other must be collections.Mapping type, not %s"%
                            other.__class__.__name__)
        diff = ExtensibleTree() if getdiff else None
        for key, value in other.items():
            if key in self.__info:
                # Update case
                oldvalue = self.__info[key]
                if isinstance(value, ExtensibleTree):
                    if isinstance(oldvalue, ExtensibleTree):
                        inner = oldvalue.update(value, getdiff)
                        if getdiff:
                            for action in ("updated", "added"): 
                                if action in inner: 
                                    diff[action][key] = inner[action]
                    else:
                        if getdiff: 
                            diff["updated"][key] = NonRecursiveNode(value.flatten())
                        self[key] = value
                elif isinstance(value, NonRecursiveNode):
                    if getdiff: diff["updated"][key] = value
                    self[key] = ExtensibleNode(value.flatten())
                elif oldvalue!=value: 
                    if getdiff: diff["updated"][key] = value
                    self[key] = value
            # Add case
            elif isinstance(value, ExtensibleTree):
                if getdiff: 
                    diff["added"][key] = NonRecursiveNode(value.flatten())
                self[key] = value
            elif isinstance(value, NonRecursiveNode):
                if getdiff: 
                    diff["added"][key] = value
                self[key] = ExtensibleTree(value.flatten())
            else:
                if getdiff: diff["added"][key] = value
                self[key] = value
        return diff

    def remove(self, other, getdiff=False):
        """Remove tree's nodes pointed by any path in 'other'.
        'other's leaf values are not considered. If 'getdiff' is True
        the diff tree is returned, otherwise None is returned."""
        if not isinstance(other, ExtensibleTree):
            raise TypeError("other must be ExtensibleTree, not %s"%
                            other.__class__.__name__)
        diff = ExtensibleTree() if getdiff else None
        for key, value in other.items():
            if key in self.__info:
                oldvalue = self.__info[key]
                if isinstance(value, ExtensibleTree) \
                        and isinstance(oldvalue, ExtensibleTree):
                    inner = oldvalue.remove(value, getdiff)
                    if getdiff and inner: 
                        diff["removed"][key] = inner["removed"]
                else:
                    if getdiff:
                        if isinstance(oldvalue, ExtensibleTree):
                            oldvalue = NonRecursiveNode(oldvalue.flatten())
                        diff["removed"][key] = oldvalue
                    del self.__info[key]
        return diff        

    def difference_update(self, other):
        """Update the tree, removing paths found in 'other'."""
        if not isinstance(other, ExtensibleTree):
            raise TypeError("other must be ExtensibleTree, not %s"%
                            other.__class__.__name__)
        changed = False
        for key, value in other.items():
            if key in self.__info:
                oldvalue = self.__info[key]
                if isinstance(value, ExtensibleTree) \
                        and isinstance(oldvalue, ExtensibleTree):
                    changed = oldvalue.difference_update(value)
                    if changed and not oldvalue: 
                        del self.__info[key]
                else:
                    changed = True
                    del self.__info[key]
        return changed

    # ---------------------------------------------------------------------
    #  Customizing attribute access

    def __getattr__(self, key):
        if key=="_NonRecursiveNode__info":
            return object.__getattribute__(self, key)
        else:
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
                "Can't set attribute '%s': name already used by %s"%(
                    key, self.__class__.__name__))
        else:
            # add
            self.__info[key] = value

    def __delattr__(self, key):
        if key in self.__class__.__dict__:
            raise AttributeError(
                "Cannot remove item '%s': name reserved by %s"%(
                    key, self.__class__.__name__))
        else:
            try:
                del self.__info[key]
            except KeyError as err:
                raise AttributeError(err)

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
            try:
                self.__setattr__(key, value)
            except AttributeError as err:
                raise KeyError(err)
        for k in self.keys(key):
            self.__info[k] = value

    def __delitem__(self, key):
        if isinstance(key, str) and key.isidentifier() or isinstance(key, int):
            try:
                self.__delattr__(key)
            except AttributeError as err:
                raise KeyError(err)
        for k in self.keys(key):
            del self.__info[k]

    def __contains__(self, path):
        """'path' can be a single string or integer or event the path
        to a tree node or leaf."""
        if isinstance(path, str) or isinstance(path, int): 
            return path in self.__info
        else:
            level = self
            for k in path:
                if not isinstance(level, ExtensibleTree) or k not in level:
                    return False
                else:
                    level = level[k]
            else:
                return True

# -------------------------------------------------------------------

class ExtensibleTree(NonRecursiveNode):
    """Recursive Node."""
    pass
    

