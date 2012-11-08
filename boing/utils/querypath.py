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

"""The module :mod:`boing.utils.querypath` provides *Querypath*, a query
language that can be used to handle hierarchical data structures, no
matter if they are composed of standard containers, e.g. :class:`list`
or :class:`dict`, or instances of standard or custom classes.

The proposed *querypath* language is a derivation of JSONPath_, which
was proposed by Stefan Goessner to handle JSON_ structures. Beyond
some minor changes, the |boing|'s query language exploits the fact
that the attributes of Python class instances are stored inside the
attribute ``__dict__``, by actually treating the instances of not
Container classes as they were dictionaries.

The root object is indexed using the character ``$``, but it can be
omitted.

*Querypath* expressions can use the dot–notation::

   contacts.0.x

or the bracket–notation::

   ['contacts'][0]['x']

or a mix of them::

   contacts[0][x]

*Querypath* allows the wildcard symbol ``*`` for member names and
array indices, the descendant operator ``..`` and the array slice
syntax ``[start:end:step]``.

Python expressions can be used as an alternative to explicit names or
indices using the syntax ``[(<expr>)]``, as for example::

   contacts[(@.__len__()-1)].x

using the symbol ``@`` for the current object. Also consider that
built-in functions and classes are not available. Filter expressions
are supported via the syntax ``[?(<boolean expr>)]`` as in::

   contacts.*[?(@.x<10)]

In order to access to multiple items that have the same parent, it is
possible to use the operator ``,``, as in::

   props.width,height

while for selecting multiple items that have different parents, it is
necessary to combine two *Querypaths* using the operator ``|``, as
in::

   props.*|contact..x

Note that the ``,`` structure is normally quicker than the ``|``
structure, since in the latter case the query always restarts from the
root object. Indexing all the values of the data model is possible
using the path ``..*``.

The module :mod:`boing.utils.querypath` provides a set of static
functions for executing *Querypath* expression on user data
structures. The query expression must be provided as standard strings.

Usage examples
==============

   >>>   class Contact:
   ...      def __init__(self, x, y):
   ...         self.x = x
   ...         self.y = y
   ...      def polar(self):
   ...         return math.sqrt(x*x, y*y), math.atan2(y,x)
   ...      def __repr__(self):
   ...         return "Contact(%s,%s)"%(self.x, self.y)
   ...
   >>>   class Surface:
   ...      def __init__(self):
   ...         self.contacts = []
   ...         self.props = {}
   ...
   >>> table = Surface()
   >>> table.props['width'] = 800
   >>> table.props['height'] = 600
   >>> table.props['id'] = "mytable"
   >>> table.contacts.append(Contact(100,200))
   >>> table.contacts.append(Contact(500,600))
   >>> tuple(querypath.get(table, "contacts.0.x"))
   (100,)
   >>> tuple(querypath.get(table, "contacts.*.x"))
   (100, 500)
   >>> tuple(querypath.get(table, "props.width,height"))
   (600, 800)
   >>> tuple(querypath.get(table, "..y"))
   (200, 600)
   >>> tuple(querypath.get(table, "contacts.*[?(@.x<=100)]"))
   (Contact(100,200),)
   >>> tuple(querypath.get(table, "contacts.*.x,y|props.*"))
   (600, 500, 800, 200, 100, 600, "mytable")
   >>> tuple(querypath.paths(table, "props.*"))
   ('props.height', 'props.width')
   >>> tuple(querypath.items(table, "contacts.*"))
   (('contacts.1', Contact(100,200)), ('contacts.2', Contact(500,600)))
   >>> querypath.test(table, "props.dpi")
   False
   >>> querypath.test(table, "contacts.*[?(@.x>100)]")
   True
   >>> querypath.test(table, "props.width.mm")
   False
   >>> querypath.test(table, "props.width.mm", wildcard=800)
   True

"""

import collections
import copy
import itertools
import re

from boing.utils import assertIsInstance

NOWILDCARD = object()
"""Option specifing that the method :func:`test` should not consider
any wildcard."""

def get(obj, path):
    """Return an iterator over the *obj*'s attributes or items
    matched by *path*."""
    return QPath(path).get(obj)

def set_(obj, path, value, tocopy=False):
    """Set the value of *obj* indexed by *path* to *value*. Return
    *obj* if *tocopy* is ``False``, otherwise the copy of *obj* where
    the modification is applied."""
    return QPath(path).set(obj, value, tocopy)

def paths(obj, path):
    """Return an iterator over the paths that index the *obj*'s
    attributes or items matched by *path*."""
    return QPath(path).paths(obj)

def items(obj, path):
    """Return an iterator over the pairs (path, value) of the
    *obj*'s items that are matched by *path*."""
    return QPath(path).items(obj)

def test(obj, path, wildcard=NOWILDCARD):
    """Return whether at least one *obj*'s attributes or items is
    matched by *path*. The object *wildcard* matches even if *path* does
    not completely match an item in obj."""
    return QPath(path).test(obj, wildcard)

# -------------------------------------------------------------------

class QPath:

    """A compiled *Querypath* expression.

    *Usage example*::

       >>> query = querypath.QPath("contacts.*.x")
       >>> tuple(query.get(table))
       (100, 500)
       >>> tuple(query.paths(table))
       ('contacts.0.x', 'contacts.1.x')
       >>> tuple(query.items(table))
       (('contacts.0.x', 100), ('contacts.1.x', 500))
       >>> query.test(table)
       True

    :class:`QPath` instances can be combined using the ``+``
    operator. This operation concatenates the operand strings using the
    ``|`` delimiter, but it also tries to optimize the result by
    avoiding expression duplicates, as in::

       >>> querypath.QPath("props")+querypath.QPath("contacts")
       QPath('contacts|props')
       >>> querypath.QPath("props")+querypath.QPath("props")
       QPath('props')

    Still it cannot optimize more complex overlaps::

       >>> querypath.QPath("contacts[0]")+querypath.QPath("contacts.*")
       QPath('contacts[0]|contatcs.*')
    """

    def __init__(self, path):
        assertIsInstance(path, str, QPath)
        self.__str = str(path)
        self._norm = _normalize(self.__str)

    def get(self, obj):
        """Return an iterator over the *obj*'s attributes or items
        matched by this QPath."""
        matches = dict(itertools.chain(*map(QPath._trace,
                                            self._norm,
                                            itertools.repeat(obj),
                                            itertools.repeat('$'),
                                            itertools.repeat(QPath._ITEMS))))
        return matches.values()

    def paths(self, obj):
        """Return an iterator over the paths that index the *obj*'s
        attributes or items matched by this QPath."""
        return iter(set(itertools.chain(*map(QPath._trace,
                                        self._norm,
                                        itertools.repeat(obj),
                                        itertools.repeat('$'),
                                        itertools.repeat(QPath._PATHS)))))

    def items(self, obj):
        """Return an iterator over the pairs (path, value) of the
        *obj*'s items that are matched by this QPath."""
        matches = dict(itertools.chain(*map(QPath._trace,
                                            self._norm,
                                            itertools.repeat(obj),
                                            itertools.repeat('$'),
                                            itertools.repeat(QPath._ITEMS))))
        return matches.items()

    def test(self, obj, wildcard=NOWILDCARD):
        """Return whether this QPath matches at least one *obj*'s
        attributes or items. The object *wildcard* matches even if
        *path* does not completely match an item in obj."""
        for singlepath in self._norm:
            for i in QPath._trace(singlepath, obj, "$", QPath._TEST, wildcard):
                return True
        return False

    def set(self, obj, value, tocopy=False):
        """Set the value of *obj* indexed by this QPath to
        *value*. Return *obj* if *tocopy* is ``False``, otherwise the
        copy of *obj* where the modification is applied."""
        rvalue = obj
        for singlepath in self._norm:
            if not singlepath: raise ValueError(
                "method QPath.set: path cannot be empty.")
            rvalue = QPath._settrace(rvalue, singlepath, value, tocopy)
        return rvalue

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

    _ITEMS = object()
    _PATHS = object()
    _TEST = object()

    # ---------------------------------------------------------------

    @staticmethod
    def _trace(expr, obj, path, op, wildcard=NOWILDCARD):
        """Yield all the results matched be *expr* on *obj*. *path*
        defines the path from the original obj to the current
        considered *obj*. *op* defines the result to be yielded:
        *(path, value)* if *op* is QPath._ITEMS, *path* otherwise."""
        if not expr or obj is wildcard:
            path = path[path.find(";")+1:].replace(";", ".")
            yield (path, obj) if op is QPath._ITEMS else path
        else:
            first, sep, rest = expr.partition(";")
            if QPath._hasprop(obj, first):
                for v in QPath._trace(rest, QPath._getprop(obj, first),
                                      path+";"+first, op, wildcard):
                    yield v
                    if op is QPath._TEST: break
            elif first=="*" \
                    or (first==":" and isinstance(obj, collections.Sequence)):
                for key, value in QPath._iteritems(obj):
                    for v in QPath._trace(rest, value,
                                          path+";"+str(key), op, wildcard):
                        yield v
                        if op is QPath._TEST: break
            elif first=="..":
                stop = False
                for v in QPath._trace(rest, obj, path, op, wildcard):
                    yield v
                    if op is QPath._TEST: stop = True ; break
                if not stop:
                    for key, value in QPath._iteritems(obj):
                        if not value is obj:
                            for v in QPath._trace(expr, value,
                                                  path+";"+str(key), op, wildcard):
                                yield v
                                if op is QPath._TEST: break
            elif "," in first: # [name1,name2,...]
                for key in first.split(","):
                    for v in QPath._trace(key+";"+rest, obj,
                                          path, op, wildcard):
                        yield v
                        if op is QPath._TEST: break
            elif first.startswith("(") and first.endswith(")"): # [(expr)]
                key = QPath._eval(first, obj)
                if key is not None:
                    for v in QPath._trace(str(key)+";"+rest, obj,
                                          path, op, wildcard):
                        yield v
                        if op is QPath._TEST: break
            elif first.startswith("?(") and first.endswith(")"): # [?(expr)]
                if QPath._eval(first[1:], obj):
                    for v in QPath._trace(rest, obj, path, op, wildcard):
                        yield v
                        if op is QPath._TEST: break
            elif isinstance(obj, collections.Sequence) :
                m = _slice.match(first)
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
                                              path+";"+str(i), op, wildcard):
                            yield v
                            if op is QPath._TEST: break


    @staticmethod
    def _settrace(obj, expr, value, tocopy):
        if not expr: rvalue = value
        else:
            rvalue = obj
            first, sep, rest = expr.partition(";")
            if QPath._hasprop(obj, first):
                prop = QPath._getprop(obj, first)
                result = QPath._settrace(prop, rest, value, tocopy)
                if prop is not result:
                    rvalue = obj if not tocopy else copy.copy(obj)
                    QPath._setprop(rvalue, first, result)
            elif first=="*" \
                    or (first==":" and isinstance(obj, collections.Sequence)):
                copied = False
                for key, prop in QPath._iteritems(obj):
                    result = QPath._settrace(prop, rest, value, tocopy)
                    if prop is not result:
                        if tocopy and not copied:
                            rvalue = copy.copy(rvalue)
                            copied = True
                        QPath._setprop(rvalue, key, result)
            elif "," in first: # [name1,name2,...]
                copied = False
                for key in first.split(","):
                    if QPath._hasprop(obj, key):
                        prop = QPath._getprop(obj, key)
                        result = QPath._settrace(prop, rest, value, tocopy)
                        if prop is not result:
                            if tocopy and not copied:
                                rvalue = copy.copy(rvalue)
                                copied = True
                            QPath._setprop(rvalue, key, result)
            elif first=="..":
                copied = False
                rvalue = QPath._settrace(obj, rest, value, tocopy)
                for key, prop in QPath._iteritems(rvalue):
                    if not prop is obj:
                        result = QPath._settrace(prop, expr, value, tocopy)
                        if prop is not result:
                            if tocopy and not copied:
                                rvalue = copy.copy(rvalue)
                                copied = True
                            QPath._setprop(rvalue, key, result)
            elif first.startswith("(") and first.endswith(")"): # [(expr)]
                key = QPath._eval(first, obj)
                if key is not None:
                    rvalue = QPath._settrace(obj, str(key)+";"+rest,
                                             value, tocopy)
            elif first.startswith("?(") and first.endswith(")"): # [?(expr)]
                if QPath._eval(first[1:], obj):
                    rvalue = QPath._settrace(obj, rest, value, tocopy)
            elif isinstance(obj, collections.Sequence):
                m = _slice.match(first)
                if m:
                    l = len(obj)
                    start, end, step = m.groups()
                    start = int(start) if start else 0
                    start = max(0, start+l) if start<0 else min(l, start)
                    end = int(end) if end else l
                    end = max(0, end+l) if end<0 else min(l, end)
                    step = int(step) if step else 1
                    copied = False
                    for key in range(start, end, step):
                        prop = QPath._getprop(obj, key)
                        result = QPath._settrace(prop, rest, value, tocopy)
                        if prop is not result:
                            if tocopy and not copied:
                                rvalue = copy.copy(rvalue)
                                copied = True
                            QPath._setprop(rvalue, key, result)
            else:
                # Create a new property
                rvalue = obj if not tocopy else copy.copy(obj)
                QPath._setprop(rvalue, first,
                               QPath._settrace(dict(), rest, value, tocopy))
        return rvalue

    @staticmethod
    def _hasprop(obj, key):
        """Return whether *obj* as the property *key*."""
        if isinstance(obj, collections.Mapping):
            rvalue = key in obj
        elif isinstance(obj, collections.Sequence) and key.isdecimal():
            rvalue = len(obj)>int(key)
        elif hasattr(obj, "__dict__"):
            l = lambda k: not k.startswith("_")
            rvalue = key in filter(l, dir(obj))
        else:
            rvalue = False
        return rvalue

    @staticmethod
    def _iteritems(obj):
        """Return an iterator of the pairs (key, value) obtained from
        *obj*."""
        if isinstance(obj, collections.Mapping):
            # FIXME: should be an iterator not tuple
            rvalue = tuple(obj.items())
        elif isinstance(obj, collections.Sequence):
            rvalue = enumerate(obj)
        elif hasattr(obj, "__dict__"):
            f = lambda k: not k.startswith("_")
            l = lambda k: (k, getattr(obj, k))
            rvalue = map(l, filter(f, dir(obj)))
        else:
            rvalue = iter(tuple())
        return rvalue

    @staticmethod
    def _getprop(obj, key):
        """Return the value of *obj* associated to *key*."""
        if isinstance(obj, collections.Mapping):
            rvalue = obj[key]
        elif isinstance(obj, collections.Sequence):
            rvalue = obj[int(key)]
        elif hasattr(obj, "__dict__") and not key.startswith("_"):
            rvalue = getattr(obj, key)
        else:
            rvalue = None
        return rvalue

    @staticmethod
    def _setprop(obj, key, value):
        """Set the value of *obj* associated to *key* to *value*."""
        if isinstance(obj, collections.Mapping):
            obj[key] = value
        elif isinstance(obj, collections.Sequence):
            obj[int(key)] = value
        else:
            setattr(obj, key, value)

    @staticmethod
    def _eval(expr, obj):
        """Evaluate the *expr* where the characted ``@`` must be
        replaced with *obj*."""
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

_slice = re.compile("^(-?[0-9]*):(-?[0-9]*):?([0-9]*)$")

def _normalize(path):
    assertIsInstance(path, str)
    if not path or path=="$": rvalue = ("", )
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
    class Contact:
          def __init__(self, x, y):
             self.x = x
             self.y = y
          def polar(self):
             return math.sqrt(x*x, y*y), math.atan2(y,x)
          def __repr__(self):
             return "Contact(%s,%s)"%(self.x, self.y)

    class Surface:
          def __init__(self):
             self.contacts = []
             self.props = {}

    table = Surface()
    table.props['width'] = 800
    table.props['height'] = 600
    table.props['id'] = "mytable"
    table.contacts.append(Contact(100,200))
    table.contacts.append(Contact(500,600))

    testpaths = [
        "",
        "$",
        "contacts.0.x",
        "contacts.*.x",
        "props.width,height",
        "..y",
        "contacts.*[?(@.x<=100)]",
        "contacts.*.x,y|props.*",
        "..*", # all members
        ] if len(sys.argv)<2 else sys.argv[1:]
    for path in testpaths:
        qpath = QPath(path)
        print("QPATH:", path)
        print("VALUE:", tuple(qpath.get(table)))
        print("PATHS:", tuple(qpath.paths(table)))
        print("ITEMS:", tuple(qpath.items(table)))
        print("TEST:", qpath.test(table))
        print()
