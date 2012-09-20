# -*- coding: utf-8 -*-
#
# boing/utils/querypath.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import itertools
import re

from boing.utils import assertIsInstance

def get(obj, path):
    """Return a list containing the *obj*'s attributes or items
    matched by *path*."""
    return QPath(path).get(obj)

# def set(obj, path, value):
#     return QPath(path).set(obj, value)

def paths(obj, path):
    """Return a list containing the paths that index the *obj*'s
    attributes or items matched by *path*."""
    return QPath(path).paths(obj)

def items(obj, path):
    """Return a list containing the pairs (path, value) of the
    *obj*'s items that are matched by *path*."""
    return QPath(path).items(obj)

def test(obj, path):
    """Return whether at least one *obj*'s attributes or items is
    matched by *path*."""
    return QPath(path).test(obj)

# -------------------------------------------------------------------

class QPath:

    _ITEMS = object()
    _PATHS = object()
    _TEST = object()

    def __init__(self, path):
        assertIsInstance(path, str, QPath)
        self.__str = str(path)
        self._norm = _normalize(self.__str)

    def get(self, obj):
        """Return a list containing the *obj*'s attributes or items
        matched by this QPath."""
        matches = dict(itertools.chain(*map(QPath._trace,
                                            self._norm,
                                            itertools.repeat(obj),
                                            itertools.repeat('$'),
                                            itertools.repeat(QPath._ITEMS))))
        return list(matches.values())

    def paths(self, obj):
        """Return a list containing the paths that index the *obj*'s
        attributes or items matched by this QPath."""
        return set(itertools.chain(*map(QPath._trace,
                                        self._norm,
                                        itertools.repeat(obj),
                                        itertools.repeat('$'),
                                        itertools.repeat(QPath._PATHS))))

    def items(self, obj):
        """Return a list containing the pairs (path, value) of the
        *obj*'s items that are matched by this QPath."""
        matches = dict(itertools.chain(*map(QPath._trace,
                                            self._norm,
                                            itertools.repeat(obj),
                                            itertools.repeat('$'),
                                            itertools.repeat(QPath._ITEMS))))
        return list(matches.items())

    def test(self, obj):
        """Return whether this QPath matches at least one *obj*'s
        attributes or items."""
        for singlepath in self._norm:
            for i in self._trace(singlepath, obj, "$", QPath._TEST):
                return True
        return False


    def __hash__(self):
        return hash(self.__str)

    def __str__(self):
        return self.__str

    def __repr__(self):
        return "QPath('%s')"%str(self.__str)

    def __bool__(self):
        return bool(self.__str)

    def __eq__(self, other):
        return isinstance(other, QPath) \
            and sorted(self._norm)==sorted(other._norm)

    def __ne__(self, other):
        return not isinstance(other, QPath) \
            or sorted(self._norm)!=sorted(other._norm)

    def __add__(self, other):
        if not isinstance(other, QPath): return NotImplemented
        else:
            selfsplit = self.__str.split("|")
            othersplit = str(other).split("|")
            return other if self==other or self.__str in othersplit \
                else self if str(other) in selfsplit \
                else QPath("|".join(set(selfsplit).union(othersplit)))

    # ---------------------------------------------------------------

    @staticmethod
    def _trace(expr, obj, path, op):
        """Yield all the results matched be *expr* on *obj*. *path*
        defines the path from the original obj to the current
        considered *obj*. *op* defines the result to be yielded:
        *(path, value)* if *op* is QPath._ITEMS, *path* otherwise."""
        if not expr:
            path = path[path.find(";")+1:].replace(";", ".")
            yield (path, obj) if op is QPath._ITEMS else path
        else:
            first, sep, rest = expr.partition(";")
            if QPath._hasprop(obj, first):
                for v in QPath._trace(rest, QPath._getprop(obj, first),
                                      path+";"+first, op):
                    yield v
                    if op is QPath._TEST: break
            elif first=="*" \
                    or (first==":" and isinstance(obj, collections.Sequence)):
                for key, value in QPath._iterprop(obj):
                    for v in QPath._trace(rest, value, path+";"+str(key), op):
                        yield v
                        if op is QPath._TEST: break
            elif first=="..":
                stop = False
                for v in QPath._trace(rest, obj, path, op):
                    yield v
                    if op is QPath._TEST: stop = True ; break
                if not stop:
                    for key, value in QPath._iterprop(obj):
                        if value!=obj:
                            for v in QPath._trace(expr, value,
                                                  path+";"+str(key), op):
                                yield v
                                if op is QPath._TEST: break
            elif "," in first: # [name1,name2,...]
                for key in first.split(","):
                    for v in QPath._trace(key+";"+rest, obj, path, op):
                        yield v
                        if op is QPath._TEST: break
            elif first[0]=="(" and first[-1]==")": # [(expr)]
                key = QPath._eval(first, obj)
                if key is not None:
                    for v in QPath._trace(str(key)+";"+rest, obj, path, op):
                        yield v
                        if op is QPath._TEST: break
            elif first.startswith("?(") and first[-1]==")": # [?(expr)]
                for key, value in QPath._iterprop(obj):
                    if QPath._eval(first[1:], value):
                        for v in QPath._trace(rest, value,
                                             path+";"+str(key), op):
                            yield v
                            if op is QPath._TEST: break
            elif isinstance(obj, collections.Sequence) :
                m = re.match("^(-?[0-9]*):(-?[0-9]*):?([0-9]*)$", first)
                if m:
                    l = len(obj)
                    start, end, step = m.groups()
                    start = int(start) if start else 0
                    start = max(0, start+l) if start<0 else min(l, start)
                    end = int(end) if end else l
                    end = max(0, end+l) if end<0 else min(l, end)
                    step = int(step) if step else 1
                    for i in range(start, end, step):
                        for v in QPath._trace(rest, obj[i],
                                             path+";"+str(i), op):
                            yield v
                            if op is QPath._TEST: break

    @staticmethod
    def _hasprop(obj, key):
        if isinstance(obj, collections.Mapping):
            rvalue = key in obj
        elif isinstance(obj, collections.Sequence) and key.isdecimal():
            rvalue = len(obj)>int(key)
        else:
            rvalue = False # hasattr(obj, key)
        return rvalue

    @staticmethod
    def _iterprop(obj):
        if isinstance(obj, collections.Mapping):
            # FIXME: should be an iterator not tuple
            rvalue = tuple(obj.items())
        elif isinstance(obj, collections.Sequence):
            rvalue = enumerate(obj)
        #elif hasattr(obj, "__dict__"):
        #    rvalue = obj.__dict__.items()
        else:
            rvalue = []
        return rvalue

    @staticmethod
    def _getprop(obj, key):
        if isinstance(obj, collections.Mapping):
            rvalue = obj[key]
        elif isinstance(obj, collections.Sequence):
            rvalue = obj[int(key)]
        else:
            rvalue = None # getattr(obj, key)
        return rvalue

    @staticmethod
    def _eval(expr, obj):
        rvalue = None
        try:
            expr = expr.replace("@", "obj")
            rvalue = eval(expr, {'__builtins__':[]}, {"obj":obj})
        except SyntaxError as e:
            print(e)
        except Exception as e:
            pass
        return rvalue

# -------------------------------------------------------------------

_re0 = re.compile("[\['](\??\(.*?\))[\]']")
_re1 = re.compile("'?\.'?|\['?")
_re2 = re.compile(";;;|;;")
_re3 = re.compile(";$|'?\]|'$")
_re4 = re.compile("#([0-9]+)")
_re5 = re.compile("\$;|^;|[ ]+;")
_re6 = re.compile("\|;")
_re7 = re.compile("[ ]*\|[ ]*")

def _normalize(path):
    assertIsInstance(path, str)
    if not path: rvalue = (path, )
    else:
        sub = []
        def encode(match):
            m = match.group()
            sub.append(match.group()[1:-1] if m[0]=="[" and m[-1]=="]" \
                           else match.group())
            return "[#%d]"%(len(sub)-1)
        def decode(match):
            return sub.pop(0)
        path = _re0.sub(encode, path)
        path = _re1.sub(";", path)
        path = _re2.sub(";..;", path)
        path = _re3.sub("", path)
        path = _re4.sub(decode, path)
        path = _re5.sub("", path)
        path = _re6.sub("|", path)
        rvalue = tuple(_re7.split(path))
    return rvalue

# -------------------------------------------------------------------

if __name__=="__main__":
    import sys
    obj = {"store": {
            "book": [
                { "category": "reference",
                  "author": "Nigel Rees",
                  "title": "Sayings of the Century",
                  "price": 8.95
                  },
                { "category": "fiction",
                  "author": "Evelyn Waugh",
                  "title": "Sword of Honour",
                  "price": 12.99
                  },
                { "category": "fiction",
                  "author": "Herman Melville",
                  "title": "Moby Dick",
                  "isbn": "0-553-21311-3",
                  "price": 8.99
                  },
                { "category": "fiction",
                  "author": "J. R. R. Tolkien",
                  "title": "The Lord of the Rings",
                  "isbn": "0-395-19395-8",
                  "price": 22.99
                  }
                ],
            "bicycle": {
                "color": "red",
                "price": 19.95
                }
            }
           }
    testpaths = [
        "",
        "store.bicycle",
        "$.store.bicycle",
        "$['store']['bicycle']",
        "$.store.book[0].author",
        "$['store']['book'][0]['author']",
        "$.store.book[*].price",
        "$.store..price",
        "$.store.book.*.author,title",
        "$.store.book,bicycle,car..price",
        "$..book[(@.__len__()-1)]",
        #"$.store[(@.clear())]", FIXME!
        "$.store.book.*",
        "$..book[?(@['price']<10)].title",
        "$..book[?(@['isbn'])].title",
        "",
        "..price|store.book[0].price",
        ] if len(sys.argv)<2 else sys.argv[1:]
    for path in testpaths:
        qpath = QPath(path)
        print("QPATH:", path)
        print("VALUE:", qpath.get(obj))
        print("PATHS:", qpath.paths(obj))
        # print("FILTER:", qpath.filter(obj))
        print("TEST:", qpath.test(obj))
        print()
