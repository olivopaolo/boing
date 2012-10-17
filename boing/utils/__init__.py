# -*- coding: utf-8 -*-
#
# boing/utils/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.


"""The module :mod:`boing.utils` contains generic utility
classes and functions.

"""

from code import InteractiveConsole
import collections
import copy
import sys

from PyQt4 import QtCore

def assertIsInstance(obj, *valid):
    """Raise TypeError if *obj* is not an instance of a class in *valid*."""
    classes = tuple(map(lambda t: type(None) if t is None else t, valid))
    if not isinstance(obj, classes): raise TypeError(
        "Expected type %s, not '%s'"%(
            " or ".join(map(lambda t: "None" if t is type(None) else t.__name__,
                            classes)),
            type(obj).__name__))
    return obj

# -------------------------------------------------------------------

class quickdict(dict):

    def __getattr__(self, key):
        if key in self: return self[key]
        elif isinstance(key, str) and key.startswith("__"):
            raise AttributeError(key)
        else:
            rvalue = quickdict()
            self[key] = rvalue
            return rvalue

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        if key in self: del self[key]
        else:
            dict.__delattr__(self, key)

    def __getitem__(self, key):
        if key in self or isinstance(key, str) and key.startswith("__"):
            return dict.__getitem__(self, key)
        else:
            rvalue = quickdict()
            self[key] = rvalue
            return rvalue

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return quickdict(self)

    def __deepcopy__(self, memo):
        ref = id(self)
        if ref in memo:
            rvalue = memo[ref]
        else:
            rvalue = quickdict()
            memo[ref] = rvalue
            for key, value in self.items():
                rvalue[key] = copy.deepcopy(value, memo)
        return rvalue

    def __repr__(self):
        return "quickdict(%s)"%dict.__repr__(self)

# -------------------------------------------------------------------

def deepadd(obj, other, diff=False, reuse=False):
    rvalue = quickdict() if diff else None
    for key, value in other.items():
        if key in obj:
            # Inner case
            objvalue = obj[key]
            if isinstance(value, collections.Mapping) \
                    and isinstance(objvalue, collections.Mapping):
                inner = deepadd(objvalue, value, diff, reuse)
                if inner: rvalue[key] = inner
        else:
            obj[key] = value if reuse else copy.deepcopy(value)
            if diff: rvalue[key] = value
    return rvalue


def deepupdate(obj, other, diff=False, reuse=False):
    rvalue = quickdict() if diff else None
    for key, value in other.items():
        if key in obj:
            # Inner case
            objvalue = obj[key]
            if isinstance(value, collections.Mapping) \
                    and isinstance(objvalue, collections.Mapping):
                inner = deepupdate(objvalue, value, diff, reuse)
                if inner: rvalue[key] = inner
            elif objvalue!=value:
                obj[key] = value if reuse else copy.deepcopy(value)
                if diff: rvalue[key] = value
        else:
            obj[key] = value if reuse else copy.deepcopy(value)
            if diff: rvalue[key] = value
    return rvalue


def deepremove(obj, other, diff=False):
    rvalue = quickdict() if diff else None
    for key, value in other.items():
        if key in obj:
            # Inner case
            objvalue = obj[key]
            if isinstance(value, collections.Mapping) \
                    and isinstance(objvalue, collections.Mapping):
                inner = deepremove(objvalue, value, diff)
                if inner: rvalue[key] = inner
            else:
                del obj[key]
                if diff: rvalue[key] = None
    return rvalue


# -------------------------------------------------------------------

class StateMachine:

    def __init__(self, initial=None):
        """The :class:`StateMachine` class defines an object that owns
        a state defined by a :class:`collections.Mapping` type
        object. The argument *initial* can be used to define the
        initial state."""
        self._state = quickdict(initial) \
            if isinstance(initial, collections.Mapping) \
            else quickdict()

    def state(self):
        """Return the current state."""
        return self._state

    def setState(self, update=None, add=None, remove=None):
        """Change the current state by applying *update*, *add* and
        *remove*."""
        diff = quickdict()
        if add is not None: diff.added = add
        if update is not None: diff.updated = update
        if remove is not None: diff.removed = remove
        self.applyDiff(diff)

    def applyDiff(self, diff, feedback=False):
        """Apply the provided *diff* to the current state. *diff* must
        be a :class:`collections.Mapping` type containing any of the following keys:

        * 'add': items that will be added to the current state;
        * 'update' : items that will be update or added to the current state;
        * 'remove' : items that will be removed from the current state.

        If feedback is ``True`` the diff structure between the
        previous state and the current state is provided as result of
        the method."""
        rvalue = None
        if feedback:
            rvalue = quickdict()
            if "added" in diff:
                added = deepadd(self._state, diff["added"], True)
                if added is not None: rvalue.added = added
            if "updated" in diff:
                updated = deepupdate(self._state, diff["updated"], True)
                if updated is not None: rvalue.updated = updated
            if "removed" in diff:
                removed = deepremove(self._state, diff["removed"], True)
                if removed is not None: rvalue.removed = removed
        else:
            if "added" in diff: deepadd(self._state, diff["added"])
            if "updated" in diff: deepupdate(self._state, diff["updated"])
            if "removed" in diff: deepremove(self._state, diff["removed"])
        return rvalue

# class StateNode(Node, StateMachine):
#     """Everytime the state changes, the diff is posted as a product."""

#     def __init__(self, initial=None, request=None, parent=None):
#         #FIXME: set productoffer
#         Node.__init__(self, request=request, parent=parent)
#         StateMachine.__init__(self, initial)

#     def applyDiff(self, diff, additional=None):
#         realdiff = StateMachine.applyDiff(self, diff, True)
#         if realdiff:
#             product = quickdict({"diff":diff})
#             if additional is not None: product.update(additional)
#             self._postProduct(product)

# if __name__ == '__main__':
#     import sys
#     from PyQt4 import QtCore
#     from boing.nodes.debug import DumpNode
#     app = QtCore.QCoreApplication(sys.argv)
#     QtCore.QTimer.singleShot(10000, app.quit)
#     m = StateNode({"contacts":{}})
#     obs = []
#     obs.append(DumpNode("diff"))
#     obs.append(DumpNode(request="diff.*.contacts.1"))
#     obs.append(DumpNode(request="diff.removed"))
#     for o in obs:
#         o.subscribeTo(m)
#         o.dumpdest = True
#     QtCore.QTimer.singleShot(
#         1000, lambda: m.setState(add={"contacts": {"1": {"pos":(0,0)}}}))
#     QtCore.QTimer.singleShot(
#         2000, lambda: m.setState(update={"contacts": {"1": {"pos":(1,2)}}}))
#     QtCore.QTimer.singleShot(
#         3000, lambda: m.setState(add={"contacts": {"3": {"pos":(0,0)}}},
#                                  update={"contacts": {"1": {"pos":(12,1)}}}))
#     QtCore.QTimer.singleShot(
#         5000, lambda: m.setState(update={"contacts": {"3": {"pos":(6,5)}}},
#                                  remove={"contacts": {"1": None}}))
#     QtCore.QTimer.singleShot(
#         7000, lambda: m.setState(remove={"contacts": {"3": None}}))
#     # Run
#     print("Initial state:", m.state())
#     rvalue = app.exec_()
#     print("Final state:", m.state())
#     sys.exit(rvalue)


# -------------------------------------------------------------------

def deepDump(obj, fd=sys.stdout, maxdepth=None, indent=2, end="\n", sort=True):
    """Write to *fd* a textual representation of *obj*."""
    _deepDump(obj, fd, 1, maxdepth, indent, end, sort)

def _deepDump(obj, fd, level, maxdepth, indent, end, sort):
    b = " "*(level*indent)
    if isinstance(obj, list) or isinstance(obj, tuple):
        print("[", end="", file=fd)
        if not obj:
            print("]", end=end, file=fd)
        elif maxdepth is None or level<=maxdepth:
            if len(obj)>1: print(end=end, file=fd)
            for i, value in enumerate(obj):
                if len(obj)>1: print(b, end="", file=fd)
                if (isinstance(value, list) or isinstance(value, tuple) \
                        or isinstance(value, collections.Mapping)) \
                        and value or hasattr(value, "__dict__"):
                    _deepDump(value, fd, level+1, maxdepth, indent, end, sort)
                else:
                    print(repr(value), end="", file=fd)
                if len(obj)>1: print(",", end="", file=fd)
                if i<len(obj)-1:
                    print(end=end, file=fd)
                elif len(obj)>1:
                    print(end+" "*((level-1)*indent), end="", file=fd)
            print("]", end="", file=fd)
        else:
            print("...]", end="", file=fd)
    elif isinstance(obj, collections.Mapping):
        print("{", end="", file=fd)
        if sort:
            keys = list(obj.keys())
            keys.sort()
        else:
            keys = obj.keys()
        if not obj:
            print("}", end=end, file=fd)
        if maxdepth is None or level<=maxdepth:
            if len(obj)>1: print(end=end, file=fd)
            for i, key in enumerate(keys):
                if len(obj)>1: print(b, end="", file=fd)
                value = obj[key]
                if (isinstance(value, list) or isinstance(value, tuple) \
                        or isinstance(value, collections.Mapping)) \
                        and value or hasattr(value, "__dict__"):
                    print("%s: "%repr(key), end="", file=fd)
                    _deepDump(value, fd, level+1, maxdepth, indent, end, sort)
                else:
                    print("%s: %s"%(repr(key), repr(value)), end="", file=fd)
                if len(obj)>1: print(",", end="", file=fd)
                if i<len(obj)-1:
                    print(end=end, file=fd)
                elif len(obj)>1:
                    print(end+" "*((level-1)*indent), end="", file=fd)
            print("}", end="", file=fd)
        else:
            print("...}", end="", file=fd)
    elif hasattr(obj, "__dict__"):
        print("%s -> "%type(obj).__name__, end="", file=fd)
        _deepDump(getattr(obj, "__dict__"), fd, level, maxdepth, indent, end, sort)
    else:
        # All other objects
        print(repr(obj), end="", file=fd)
    if level==1: print(end=end, file=fd)

# -------------------------------------------------------------------

class Console(InteractiveConsole, QtCore.QObject):
    """Interactive Python console running along the Qt eventloop.

    """

    class _FileCacher:
        """Cache the output text so we can analyze it before writing it."""
        def __init__(self): self.reset()
        def reset(self): self.out = []
        def write(self,line): self.out.append(line)
        def flush(self):
            output = ''.join(self.out)
            self.reset()
            return output

    ps1 = ">>> "
    ps2 = "... "

    def __init__(self, inputdevice, outputdevice, banner="",
                 locals=None, parent=None):
        InteractiveConsole.__init__(self, locals=locals)
        QtCore.QObject.__init__(self, parent)
        # Backup of the current stdout and stderr
        self._backup = sys.stdout
        self._cache = Console._FileCacher()
        self.__in = inputdevice
        self.__in.readyRead.connect(self._readAndPush)
        self.__out = outputdevice
        self.banner = banner
        if self.__out.isOpen(): self._writeBanner()
        elif hasattr(self.__output, "connected"):
            self.__out.connected.connect(self._writeBanner())

    def _readAndPush(self):
        """Read from the input device and interpret the command"""
        data = self.__in.read()
        if not data:
            print()
            QtCore.QCoreApplication.instance().quit()
        else:
            text = data if self.__in.isTextModeEnabled() else data.decode()
            self.push(text)

    def _pushStd(self):
        """Replace stdout and stderr, so that the current console's
        output can be redirected."""
        self._backup = (sys.stdout, sys.stderr)
        sys.stdout = sys.stderr = self._cache

    def _pullStd(self):
        """Restore previous stdout and stderr."""
        sys.stdout, sys.stderr = self._backup

    def push(self, line):
        """Pass *line* to the Python interpreter."""
        self._pushStd()
        more = super().push(line)
        self._pullStd()
        self._write(Console.ps2 if more else self._cache.flush()+Console.ps1)
        return more

    def _writeBanner(self):
        self._write(self.banner)
        self._write(Console.ps1)

    def _write(self, text):
        """Write *text* to the output device."""
        self.__out.write(text if self.__out.isTextModeEnabled() \
                                   else text.encode())
        self.__out.flush()
