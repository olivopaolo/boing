# -*- coding: utf-8 -*-
#
# boing/nodes/debug.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import datetime
import io
import sys
import weakref

from PyQt4 import QtCore

import boing.utils as utils

from boing.core.OnDemandProduction import OnDemandProducer
from boing.core.MappingEconomy import \
    MappingProducer, HierarchicalProducer, HierarchicalConsumer, \
    Node, FilterOut
from boing.core.ProducerConsumer import Producer, Consumer
import boing.utils.fileutils as fileutils

class DumpNode(Node):

    def __init__(self, src=False, dest=False, depth=None, 
                 request=OnDemandProducer.ANY_PRODUCT, hz=None, parent=None):
        Node.__init__(self, request=request, hz=hz, parent=parent)
        if not isinstance(src, bool): raise TypeError(
            "src must be boolean, not '%s'"%src.__class__.__name__)
        self.dumpsrc = src
        if not isinstance(dest, bool): raise TypeError(
            "dest must be boolean, not '%s'"%dest.__class__.__name__)
        self.dumpdest = dest
        self.depth = None if depth is None else int(depth) 

    def _consume(self, products, producer):
        stream = io.StringIO()
        if self.dumpsrc: 
            stream.write("from: %s\n"%str(producer))
        if self.dumpdest: 
            stream.write("DumpNode(request=%s)\n"%repr(str(self.request())))
        for p in products:
            utils.deepDump(p, stream, self.depth)
        stream.write("\n")
        self._postProduct({'str': stream.getvalue()})

# -------------------------------------------------------------------

'''class RenameNode(Node):

    def __init__(self, request, rename, target=None,
                 productoffer=None, hz=None, parent=None):
        Node.__init__(self, productoffer, request=request, hz=hz, parent=parent)
        self.rename = rename
        self.target = target if target is not None else request

    def _consume(self, products, producer):
        for p in products:
            if isinstance(p, collections.Mapping) and self.target in p: 
                self._postProduct({self.rename: p[self.target]})'''

# -------------------------------------------------------------------

class Timer(HierarchicalProducer):

    def __init__(self, *args, **kwargs):
        # FIXME: set productoffer
        HierarchicalProducer.__init__(self, *args, **kwargs)
        self.__timer = QtCore.QTimer()
        self.__timer.timeout.connect(self.__timeout)

    def start(self, msec=None):
        self.__timer.start() if msec is None else self.__timer.start(msec)

    def stop(self):
        self.__timer.stop()

    def interval(self):
        return self.__timer.interval()

    def isActive(self):
        return self.__timer.isActive()

    def isSingleShot(self):
        return self.__timer.isSingleShot()

    def setInterval(self, msec):
        self.__timer.setInterval(msec)

    def setSingleShot(self, singleShot):
        self.__timer.setSingleShot(singleShot)

    def timerId(self):
        return self.__timer.timerId()

    @QtCore.pyqtSlot()
    def __timeout(self):
        self._postProduct({"timeout":None})

# -------------------------------------------------------------------

class StatProducer(Node):

    class StatRecord(object):
        def __init__(self):
            self.tot = 0
            self.partial = 0
            self.tags = set()
            self.lagmax = None

    def __init__(self, request=OnDemandProducer.ANY_PRODUCT, 
                 hz=1, inhz=None, parent=None):
        #FIXME: set productoffer
        Node.__init__(self, request=request, hz=inhz)
        self.__timer = QtCore.QTimer(timeout=self.__produce)        
        self.__timer.start(1000/float(hz))
        self._inittime = datetime.datetime.now()
        self.__stat = {}
        self._update = False
        self._addTag("str", {"str": str()})

    def _checkRef(self):
        Node._checkRef(self)
        self.__stat = dict((k, v) for k, v in self.__stat.items() \
                                   if k() is not None)

    def _removeObservable(self, observable):
        Node._removeObservable(self, observable)
        for ref in self.__stat.keys():
            if ref() is observable: 
                del self.__sources[ref] ; break

    def _consume(self, products, producer):
        self._update = True
        # Get producer record
        record = None
        for ref, rec in self.__stat.items():
            if ref() is producer: record = rec ; break
        else:
            record = StatProducer.StatRecord()
            self.__stat[weakref.ref(producer)] = record
        # Update record
        now = datetime.datetime.now()
        for p in products:
            record.partial += 1
            record.tags.update(p.keys())
            if "timetag" in p:
                timetag = p["timetag"]
                if timetag is not None:
                    delta = now - timetag
                    if record.lagmax is None or delta>record.lagmax:
                        record.lagmax = delta

    def __produce(self):
        if self._update and self._tag("str"):
            self._update = False
            data = io.StringIO()
            intro = False
            for ref, record in self.__stat.items():
                if record.partial>0:
                    if not intro:
                        delta = datetime.datetime.now() - self._inittime
                        data.write("Statistics after %s\n"%delta)
                        intro = True
                    record.tot += record.partial
                    data.write(str(ref()))
                    data.write("\n")
                    data.write("  tags: %s\n"%record.tags)
                    if record.lagmax is not None:
                        msecs = record.lagmax.seconds*1000 \
                            +record.lagmax.microseconds/1000
                        record.lagmax = None
                        data.write("  tot=%d, hz=%g, lagmax=%f ms\n"%(
                                record.tot, 
                                record.partial*1000/self.__timer.interval(), 
                                msecs))
                    else:
                        data.write("  tot=%d, hz=%d\n"%(record.tot, record.partial))
                    record.partial = 0
                    record.tags.clear()
            if intro: data.write("\n")
            self._postProduct({"str": data.getvalue()})

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

def dumpGraph(origins, fd=sys.stdout, maxdepth=None, indent=4):
    # print("dumpGraph", origins, fd)
    memo = []
    for node in origins:
        dumpNode(node, memo, fd, 0, maxdepth, indent)


def dumpNode(node, memo, fd, level, maxdepth, indent):
    # print("dumpNode", memo, fd)
    if memo is None: memo = []
    if node in memo:
        fd.write("Node: %d"%memo.index(node))
    else:
        memo.append(node)
        base = " "*(level*indent)
        fd.write(base+"%d: %s\n"%(len(memo), type(node)))
        if isinstance(node, Consumer):
            request = node.request()
            if request is not None: request = repr(str(request))
            fd.write(base+"  request = %s\n"%request)
            if isinstance(node, FilterOut):
                filterout = node.request()
                if filterout is not None: filterout = repr(str(filterout))
                fd.write(base+"  filterout = %s\n"%filterout)
            if isinstance(node, HierarchicalConsumer):
                fd.write(base+"  pre = [")
                if not node.pre():
                    fd.write("]\n")
                elif maxdepth is None or level<maxdepth:
                    fd.write(base+"\n\n")                
                    for pre in node.pre():
                        dumpNode(pre, memo, fd, level+1, maxdepth, indent)
                    fd.write(base+"  ]\n")                
                else:
                    fd.write("...]\n")
                baserequest = node._baserequest
                if baserequest is not None: baserequest = repr(str(baserequest))
                fd.write(base+"  _baserequest = %s\n"%baserequest)
        if isinstance(node, Producer):
            if isinstance(node, MappingProducer):
                if isinstance(node, HierarchicalProducer):
                    fd.write(base+"  post = [")
                    if not node.post():
                        fd.write("]\n")
                    elif maxdepth is None or level<maxdepth:
                        fd.write(base+"\n\n")                
                        for post in node.post():
                            dumpNode(post, memo, fd, level+1, maxdepth, indent)
                        fd.write(base+"  ]\n")                
                    else:
                        fd.write("...]\n")
                demand = node.aggregateDemand()
                if demand is not None: demand = repr(str(demand))
                fd.write(base+"  aggregateDemand = %s\n"%demand)
            fd.write(base+"  observers = [")
            if not node.observers():
                fd.write(base+"]\n\n")
            elif maxdepth is None or level<maxdepth:
                fd.write(base+"\n\n")                
                for observer in node.observers():
                    dumpNode(observer, memo, fd, level+1, maxdepth, indent)
                fd.write(base+"  ]\n")
            else:
                fd.write("...]\n\n")
                
