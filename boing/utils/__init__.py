# -*- coding: utf-8 -*-
#
# boing/utils/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import copy
import itertools
import sys

from PyQt4 import QtCore

class quickdict(dict):

    def __getattr__(self, key):
        if key in self: return dict.__getitem__(self, key)
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
        if key in self: return dict.__getitem__(self, key)
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
        if ref in memo: rvalue = memo[ref]
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

def deepDump(obj, fd, maxdepth=None, indent=4):
    return _deepDump(obj, fd, 0, maxdepth, indent)

def _deepDump(obj, fd, level, maxdepth, indent):
    if isinstance(obj, list) or isinstance(obj, tuple):
        print("%s["%(" "*level*indent), end="", file=fd)
        if maxdepth is None or level<maxdepth:
            for i, value in enumerate(obj):
                if (isinstance(value, list) or isinstance(value, tuple) \
                        or isinstance(value, collections.Mapping)) \
                        and value:
                    print("", file=fd)
                    _deepDump(value, fd, level+1, maxdepth, indent)
                else:
                    if i>0: print(" "*(level*indent+1), end="", file=fd)
                    print(repr(value), end="", file=fd)
                if i<len(obj)-1: print(",", file=fd)
            print("]", end="", file=fd)
        else:
            print("...]", end="", file=fd)
    elif isinstance(obj, collections.Mapping):
        print("%s{"%(" "*level*indent), end="", file=fd)
        keys = list(obj.keys())
        keys.sort()
        if maxdepth is None or level<maxdepth:
            for i, key in enumerate(keys):
                value = obj[key]
                if i>0: print(" "*(level*indent+1), end="", file=fd)
                if (isinstance(value, list) or isinstance(value, tuple) \
                        or isinstance(value, collections.Mapping)) \
                        and value:
                    print("%s:"%repr(key), file=fd)
                    _deepDump(value, fd, level+1, maxdepth, indent)
                else:
                    print("%s: %s"%(repr(key), repr(value)), end="", file=fd)
                if i<len(obj)-1: print(",", file=fd)
            print("}", end="", file=fd)
        else:
            for i, key in enumerate(keys):
                if i>0: print(" "*(level*indent+1), end="", file=fd)
                print("%s: ..."%repr(key), end="", file=fd)
                if i<len(obj)-1:
                    print(",", file=fd)
            print("}", end="", file=fd)
    else:
        print(repr(obj), file=fd)
    if level==0: print(file=fd)

# -------------------------------------------------------------------

class Console(QtCore.QObject):

    def __init__(self, inputdevice, outputdevice, 
                 nohelp=False, parent=None):
        super().__init__(parent)
        self.__input = inputdevice
        self.__input.readyRead.connect(self.__exec)
        self.__output = outputdevice
        self.prologue = "Boing console\n"
        self.linebegin = "> "
        self.__cmd = dict()
        if not nohelp: 
            self.addCommand("help", Console.__help, 
                            help="Display available commands.", 
                            cmd=self.__cmd, fd=self.__output)
        if self.__output.isOpen(): self._startUp()
        elif hasattr(self.__output, "connected"):
            self.__output.connected.connect(self._startUp)
    
    def inputDevice(self):
        return self.__input

    def outputDevice(self):
        return self.__output

    def addCommand(self, name, func, help="", *args, **kwargs):
        self.__cmd[name] = (help, func, args, kwargs) 

    def __exec(self):
        data = self.__input.read()
        text = data if self.__input.isTextModeEnabled() else data.decode()
        command, *rest = text.partition("\n")
        if command:
            if command in self.__cmd:
                help, func, args, kwargs = self.__cmd[command]
                func(*args, **kwargs)
            else:
                self.__output.write("%s: command not found"%command)
                self.__output.flush()
        self.__output.write(self.linebegin)
        self.__output.flush()

    def _startUp(self):
        self.__output.write(self.prologue)
        if "help" in self.__cmd:
            self.__output.write("Type 'help' for the command guide.\n")
        self.__output.write(self.linebegin)
        self.__output.flush()

    @staticmethod
    def __help(cmd, fd=sys.stdout):
        for name, record in cmd.items():
            help, *rest = record
            fd.write(" %s                %s\n"%(name, help))
        fd.write("\n")

# -------------------------------------------------------------------

def assertIsInstance(obj, *valid):
    classes = tuple(map(lambda t: type(None) if t is None else t, valid))
    if not isinstance(obj, classes): raise TypeError(
        "Expected type %s, not '%s'"%(
            " or ".join(map(lambda t: "None" if t is type(None) else t.__name__, 
                            classes)), 
            type(obj).__name__))
    return obj
