# -*- coding: utf-8 -*-
#
# boing/utils/QPath.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import copy
import collections
import itertools
import re

def get(obj, path):
    """Returns the list of items of 'obj' matched by 'path'."""
    return QPath(path).get(obj)

def paths(obj, path):
    """Returns the list of paths indexing the items of 'obj' that are
    matched by 'path'."""
    return QPath(path).paths(obj)

def filter(obj, path, deepcopy=True):
    """Returns the a subset of 'obj' that is matched by 'path'."""
    return QPath(path).filter(obj, deepcopy)

def filterout(obj, path):
    return QPath(path).filterout(obj)

def test(obj, path):
    """Returns True if at least one item of 'obj' is matched by
    'path'; False otherwise."""
    return QPath(path).test(obj)

def join(*paths):
    """Returns the union of many QPaths."""
    if not paths:
        rvalue = None
    elif "*" in map(str, paths):
        rvalue = QPath("*")
    else:
        filtered = set(itertools.chain(*(
                    str(p).split("|") for p in paths if p is not None)))
        rvalue = QPath("|".join(filtered)) if filtered else None
    return rvalue

def subtract(minuend, subtrahend):
    if subtrahend is None: 
        rvalue = minuend
    elif str(subtrahend)=="*" or minuend==subtrahend: 
        rvalue = None
    else:
        difference = set(str(minuend).split("|"))-set(str(subtrahend).split("|"))
        rvalue = QPath("|".join(difference)) if difference else None
    return rvalue


class QPath(object):

    class ListPlaceholder(collections.OrderedDict):
        pass
    
    def __init__(self, path):
        if path is None: raise TypeError(
                "QPath() argument must be a string, not %s"%type(path))
        self._path = str(path)
        self._norm = QPath._normalize(self._path)
        self._resultType = None
        self._result = None
        self._target = None
        # In the case of filtering lists are replaced with
        # ListPlaceholders, so before returning the result, it is
        # necessary to reconvert them to standard lists.
        self._validate = False
        self._deepcopy = False

    def get(self, obj):
        """Returns the list of the matched items of 'obj'."""
        self._target = obj
        self._resultType = "VALUE"
        self._result = []
        for path in self._norm:
            self._trace(path, obj, "$")
        rvalue = self._result
        self._tearDown()
        return rvalue

    def paths(self, obj):        
        """Returns the list of paths indexing the matched items of 'obj'."""
        self._target = obj
        self._resultType = "COMPACTPATH"
        self._result = []
        for path in self._norm:
            self._trace(path, obj, "$")
        rvalue = self._result
        self._tearDown()
        return rvalue

    def items(self, obj):
        self._target = obj
        self._resultType = "ITEMS"
        self._result = ([], [])
        for path in self._norm:
            self._trace(path, obj, "$")
        rvalue = self._result
        self._tearDown()
        return rvalue
   
    def filter(self, obj, deepcopy=True):
        """Returns the matched subset of "obj"."""
        self._target = obj
        self._resultType = "FILTER"
        self._deepcopy = deepcopy
        self._result = None
        for path in self._norm:
            self._trace(path, obj, "$")
        rvalue = self._result
        if self._validate:
            QPath._validate(rvalue)
            if isinstance(rvalue, QPath.ListPlaceholder):
                rvalue = list(rvalue.values())
        self._tearDown()
        return rvalue

    def filterout(self, obj):
        self._target = obj
        self._resultType = "COMPACTPATH"
        self._result = []
        for path in self._norm:
            self._trace(path, obj, "$")
        for path in self._result:
            split = path.split(";")
            if not split: self._target = None ; break
            node = self._target
            for key in split[1:-1]:
                node = node[key]
            del node[split[-1]]          
        rvalue = self._target
        self._tearDown()
        return rvalue

    def test(self, obj):
        """Returns True if at least one item of 'obj' is matched;
        False otherwise."""
        self._target = obj
        self._resultType = "TEST"
        self._result = False
        for path in self._norm:
            self._trace(path, obj, "$")
            if self._result: break
        rvalue = self._result
        self._tearDown()
        return rvalue

    def _tearDown(self):
        self._target = self._result = self._resultType = None
        self._deepcopy = self._validate = False

    def _store(self, path, value):
        """Store result."""
        stop = False
        if path: 
            if self._resultType=="VALUE":
                self._result.append(value)
            elif self._resultType=="PATH":
                self._result.append(QPath._asPath(path))
            elif self._resultType=="COMPACTPATH":
                self._result.append(path)
            elif self._resultType=="ITEMS":
                path = path[path.find(";")+1:]
                self._result[0].append(path.replace(";","."))
                self._result[1].append(value)
            elif self._resultType=="FILTER":
                if path=="$":  
                    self._result = value if not self._deepcopy \
                        else copy.deepcopy(value)
                else:
                    obj = self._target
                    if self._result is None:
                        if isinstance(obj, collections.Mapping):
                            self._result = type(obj)()
                        else:
                            self._result = QPath.ListPlaceholder()
                            self._validate = True
                    result = self._result
                    split = path.split(";")
                    for key in split[1:-1]:
                        obj = obj[key if isinstance(obj, collections.Mapping) \
                                      else int(key)]
                        temp = result.get(key, None)
                        if temp is None:
                            if isinstance(obj, collections.Mapping):
                                temp = type(obj)()
                            else:
                                temp = QPath.ListPlaceholder()
                                self._validate = True
                            result[key] = temp
                        result = temp
                    result[split[-1]] = value if not self._deepcopy \
                        else copy.deepcopy(value)
            elif self._resultType=="TEST":
                self._result = stop = True
        return stop

    def _trace(self, expr, obj, path):
        """Parce query."""
        stop = False
        if expr:
            first, sep, rest = expr.partition(";")
            if QPath._hasprop(obj, first):
                stop = self._trace(rest, QPath._getprop(obj, first), 
                                   ";".join((path, first)))
            elif first=="*" \
                    or (first==":" and isinstance(obj, collections.Sequence)):
                for key, value in QPath._iterprop(obj):
                    stop = self._trace(rest, value, ";".join((path, str(key))))
                    if stop: break
            elif first=="..":
                stop = self._trace(rest, obj, path)
                if not stop:
                    for key, value in QPath._iterprop(obj):
                        if value!=obj: 
                            stop = self._trace(expr, value, 
                                               ";".join((path, str(key))))
                            if stop: break
            elif "," in first: # [name1,name2,...]
                for key in first.split(","):
                    stop = self._trace(";".join((key, rest)), obj, path)
                    if stop: break
            elif first[0]=="(" and first[-1]==")": # [(expr)]
                key = QPath._eval(first, obj)
                if key is not None:
                    stop = self._trace(";".join((str(key), rest)), obj, path)
            elif first.startswith("?(") and first[-1]==")": # [?(expr)]
                for key, value in QPath._iterprop(obj):
                    if QPath._eval(first[1:], value):
                        stop = self._trace(rest, value, 
                                           ";".join((path, str(key))))
                        if stop: break
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
                        stop = self._trace(rest, obj[i], 
                                           ";".join((path, str(i))))
                        if stop: break
        else:
            stop = self._store(path, obj)
        return stop

    @staticmethod
    def _validate(obj):
        """Convert ListPlaceholders to standard lists."""
        for k, v in obj.items():
            if isinstance(v, collections.Mapping): 
                QPath._validate(v)
                if isinstance(v, QPath.ListPlaceholder):
                    obj[k] = list(v.values())

    @staticmethod
    def _normalize(path):
        if path is None:
            rvalue = tuple()
        elif not path:
            rvalue = (path, )
        else:
            sub = []
            p0 = re.compile("[\['](\??\(.*?\))[\]']")
            def encode(match):
                m = match.group()           
                sub.append(match.group()[1:-1] if m[0]=="[" and m[-1]=="]" \
                               else match.group())
                return "[#%d]"%(len(sub)-1)
            def decode(match):
                return sub.pop(0)
            path = p0.sub(encode, path)
            p1 = re.compile("'?\.'?|\['?")
            path = p1.sub(";", path)
            p2 = re.compile(";;;|;;")
            path = p2.sub(";..;", path)
            p3 = re.compile(";$|'?\]|'$")
            path = p3.sub("", path)
            p4 = re.compile("#([0-9]+)")
            path = p4.sub(decode, path)
            p5 = re.compile("\$;")
            path = p5.sub("", path)
            p6 = re.compile("[ ]*\|[ ]*")
            rvalue = p6.split(path)
        return rvalue

    @staticmethod
    def _asPath(path):
        """Return path as string like "$['store']['book'][0]['author']". """
        x = path.split(";")
        rvalue = ["$"]
        for elem in x[1:]:
            rvalue.append("[%s]"%elem if elem.isdecimal() \
                              else "['%s']"%elem)
        return "".join(rvalue)

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
            rvalue = obj.items()
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

    def __hash__(self):
        return hash(self._path)

    def __str__(self):
        return str(self._path)

    def __repr__(self):
        return "QPath('%s')"%str(self._path)

    def __bool__(self):
        return bool(self._path)

    def __eq__(self, other):        
        return isinstance(other, QPath) and self._path==other._path

    def __ne__(self, other):
        return not isinstance(other, QPath) or self._path!=other._path

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
        ] if len(sys.argv)<2 else sys.argv[1:]
    for path in testpaths:
        qpath = QPath(path)
        print("QPATH:", path)
        print("VALUE:", qpath.get(obj))
        print("PATHS:", qpath.paths(obj))
        print("FILTER:", qpath.filter(obj))
        print("TEST:", qpath.test(obj))
        print()
