# -*- coding: utf-8 -*-
#
# boing/eventloop/EventLoop.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import collections
import signal
import sys
import time
import traceback
import uuid

from PyQt4 import QtCore

class __metaclass(type):
    
    def __new__(mcls, name, bases, dict):
        cls = type.__new__(mcls, name, bases, dict)
        cls.__mainloop = None
        return cls
        
    @property
    def mainloop(self):
        if self.__mainloop is None:
            self.__mainloop = self.__create()
        return self.__mainloop

    @staticmethod
    def __create():
        return EventLoop_PyQt()

# ----------------------------------------------------------------

class EventLoop(metaclass=__metaclass):
        
    @staticmethod
    def run_for(seconds, returnAfterSourceHandled=False):
        EventLoop.mainloop.run_for(seconds, returnAfterSourceHandled)
    @staticmethod
    def run():
        return EventLoop.mainloop.run()
    @staticmethod
    def stop():
        EventLoop.mainloop.stop()

    @staticmethod
    def after(seconds, callback, *args, **kwargs):
        return EventLoop.mainloop.after(seconds, callback, *args, **kwargs)
    @staticmethod
    def repeat_every(seconds, callback, *args, **kwargs):
        return EventLoop.mainloop.repeat_every(seconds, callback, *args, **kwargs)
    @staticmethod
    def cancel_timer(tid):
        EventLoop.mainloop.cancel_timer(tid)

    @staticmethod
    def if_readable(obj, callback, *args, **kwargs):
        return EventLoop.mainloop.if_readable(obj, callback, *args, **kwargs)
    @staticmethod
    def if_writable(obj, callback, *args, **kwargs):
        return EventLoop.mainloop.if_writable(obj, callback, *args, **kwargs)
    @staticmethod
    def cancel_fdhandler(did):
        EventLoop.mainloop.cancel_fdhandler(did)

    @staticmethod
    def when_idle(callback, *args, **kwargs):
        return EventLoop.mainloop.when_idle(callback, *args, **kwargs)
    @staticmethod
    def renew_idletask(iid, callback, *args, **kwargs):
        EventLoop.mainloop.renew_idletask(iid, callback, *args, **kwargs)
    @staticmethod
    def cancel_idletask(iid):
        EventLoop.mainloop.cancel_idletask(iid)

# ----------------------------------------------------------------

class EventLoop_PyQt(EventLoop):

    # http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qcoreapplication.html
    # http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qeventloop.html

    IDLE_TIMEOUT = 0.2
    
    def __init__(self):
        self.__app = QtCore.QCoreApplication.instance()
        if self.__app==None: self.__app = QtCore.QCoreApplication(sys.argv)
        self.__loop = QtCore.QEventLoop()
        self.__t = {}
        self.__d = {}
        self.__qObservables = {}
        signal.signal(signal.SIGINT, lambda *args, **kwargs: self.stop())
        
    def run_for(self, seconds, returnAfterSourceHandled=False):
        """
        @type seconds: number
        @param seconds: the time to run the event loop, greater or equal to 0
        @type returnAfterSourceHandled: boolean
        @param returnAfterSourceHandled: a flag indicating whether the loop should exit after processing one event source
        @rtype: string
        @return: "stopped","timedOut","handledSource" or "unknown"
        """
        if seconds<0: raise ValueError("seconds must be >= 0")
        now = starttime = time.time()
        endtime = starttime+seconds
        while now<=endtime:
            delta = endtime-now
            self.__loop.processEvents(QtCore.QEventLoop.AllEvents, 
                                      delta*1000)
            now = time.time()
            if now>endtime: return "unknown"
        return "timedOut"
    
    def run(self):
        self.repeat_every(EventLoop_PyQt.IDLE_TIMEOUT, lambda a:None)
        return self.__app.exec_()
    
    def stop(self):
        self.__app.quit()
        
    def __del__(self):
        self.stop()

    # -- Timers --------------------------------------------

    # http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qtimer.html
    
    def __createTimer(self, tid, seconds, singleshot, callback, *args, **kwargs):
        timer = QtCore.QTimer()
        timer.setSingleShot(singleshot)
        QtCore.QObject.connect(timer, QtCore.SIGNAL("timeout()"),
                                lambda timer=timer,tid=tid: self.__timerTriggered(timer,tid))
        timer.start(seconds*1000)
        self.__t[tid] = (timer, (callback, args, kwargs))
        return tid

    def __timerTriggered(self, timer, tid):
        if timer.isSingleShot():
            timer, (callback, args, kwargs) = self.__t.pop(tid)
        else:
            timer, (callback, args, kwargs) = self.__t.get(tid)
        if isinstance(callback, collections.Callable):
            try:
                callback(tid, *args,**kwargs)
            except KeyboardInterrupt:
                raise
            except:
                traceback.print_exc()

    def after(self, seconds, callback, *args, **kwargs):
        """
        @type seconds: number
        @param seconds: the time after which the callback should be called
        @type callback: callable
        @param callback: a callable that will be called using args and kwargs
        @rtype: string
        @return: a timer ID (aka tid)
        """
        return self.__createTimer("tid-%s"%uuid.uuid1(),
                                  seconds, True, callback, *args, **kwargs)
        
    def repeat_every(self, seconds, callback, *args, **kwargs):
        """
        @type seconds: number
        @param seconds: the time period at which the callback should be called
        @type callback: callable
        @param callback: a callable that will be called using args and kwargs
        @rtype: string
        @return: a timer ID (aka tid)
        """
        return self.__createTimer("tid-%s"%uuid.uuid1(),
                                  seconds, False, callback, *args, **kwargs)

    def cancel_timer(self, tid):
        """
        @type tid: string
        @param tid: ID of the timer to cancel
        """
        try:
            timer, cInfo = self.__t.pop(tid)
            timer.stop()
        except KeyError:
            pass

    # -- File descriptor handlers --------------------------

    # http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/qsocketnotifier.html

    def __sockEvent(self, did):
        fd, (obj, event), (callback, args, kwargs) = self.__d[did]            
        if isinstance(callback, collections.Callable):
            try:
                callback(did, *args, **kwargs)
            except KeyboardInterrupt:
                raise
            except:
                traceback.print_exc()

    def __createFdHandler(self, obj, event, callback, *args, **kwargs):
        if type(obj)==int:
            fileno = obj
        else:
            fileno = obj.fileno()
        did = "did-%s-%s"%(event,uuid.uuid1())
        event = QtCore.QSocketNotifier.Read if event=='r' else QtCore.QSocketNotifier.Write
        fd = QtCore.QSocketNotifier(fileno, event)
        fd.connect(fd, QtCore.SIGNAL('activated(int)'),
                   lambda i, did=did: self.__sockEvent(did))
        self.__d[did] = (fd, (obj, event), (callback, args, kwargs))
        return did

    def if_readable(self, obj, callback, *args, **kwargs):
        """
        @type obj: any object with a fileno method
        @param obj: the file-like object to be monitored
        @type callback: callable
        @param callback: a callable that will be called using args and kwargs
        @rtype: string
        @return: a descriptor ID (aka did)
        """
        return self.__createFdHandler(obj, "r", callback, *args, **kwargs)


    def if_writable(self, obj, callback, *args, **kwargs):
        """
        @type obj: any object with a fileno method
        @param obj: the file-like object to be monitored
        @type callback: callable
        @param callback: a callable that will be called using args and kwargs
        @rtype: string
        @return: a descriptor ID (aka did)
        """
        return self.__createFdHandler(obj, "w", callback, *args, **kwargs)

    def cancel_fdhandler(self, did):
        """
        @type did: string
        @param did: ID of the descriptor handler to cancel
        """
        try:
            fd, oInfo, cInfo = self.__d.pop(did)
            fd.setEnabled(False)
        except KeyError:
            pass
        
    # -- Idle tasks ----------------------------------------

    def when_idle(self, callback, *args, **kwargs):
        """
        @type callback: callable
        @param callback: a callable that will be called using args and kwargs
        @rtype: string
        @return: an idle ID (aka iid)
        """
        return self.__createTimer("iid-%s"%uuid.uuid1(),
                                  EventLoop_PyQt.IDLE_TIMEOUT, True,
                                  callback, *args, **kwargs)

    def renew_idletask(self, iid, callback, *args, **kwargs):
        """
        @type iid: string
        @param iid: ID of the idle handler to renew
        @type callback: callable
        @param callback: a callable that will be called using args and kwargs
        """
        return self.__createTimer(iid,
                                  EventLoop_PyQt.IDLE_TIMEOUT, True,
                                  callback, *args, **kwargs)
    
    def cancel_idletask(self, iid):
        """
        @type iid: string
        @param iid: ID of the idle handler to cancel
        """
        self.cancel_timer(iid)

#FIXME: auto initializer
EventLoop.mainloop
