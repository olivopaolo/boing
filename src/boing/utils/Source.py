# -*- coding: utf-8 -*-
#
# boing/utils/Source.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

from boing.tuio.TuioToState import TuioSource
from boing.url import URL

#if sys.platform=='linux2':
#    from boing.multitouch.MtDevDevice import MtDevDevice

def Source(url):
    """Create a new event source instance using the argument "url"."""
    if not isinstance(url, URL): url = URL(str(url))
    source = None
    if url.scheme.startswith("tuio"): 
        source = TuioSource(url)
        """elif url.scheme.startswith("mtdev"):
        if sys.platform == "linux2":
            if url.kind==URL.GENERIC \
               and url.scheme=="mtdev" and str(url.site)=="":
                lock = url.query.data.get('lock')
                try:
                    if lock is not None:
                        source = MtDevDevice(str(url.path), 
                                             lock= lock.lower!="false")
                    else:
                        source = MtDevDevice(str(url.path))
                except Exception:
                    traceback.print_exc()
        else:
            print("mtdev device not supported on ", sys.platform)"""
    else:
        print("Unrecognized source URL:", str(url))
    """if source is not None:
        filepath = url.query.data.get("conf")
        if filepath is not None:
            # update source's state with the config parameters
            try:
                root = ElementTree.parse(filepath).getroot()
                conf = {}
                for item in root:
                    conf[item.tag] = eval(item.text)
                for key, value in conf.items():
                    statevalue = source.state.get(key)
                    if isinstance(value, dict) \
                       and isinstance(statevalue, dict):
                        copy = statevalue.copy()
                        copy.update(value)
                        conf[key] = copy
                source.setState(**conf)
            except Exception:
                traceback.print_exc()
                print("Cannot load config file", filepath)"""
    return source
"""
def UrlToSourceClass(url):
    if not isinstance(url, URL): url = URL(str(url))
    sourceclass = None
    if url.scheme.startswith("tuio"):
        sourceclass = TuioSourceClass(url)
    elif url.scheme.startswith("mtdev"):
        if sys.platform == "linux2":
            sourceclass = MtDevDevice
        else:
            print("mtdev device not supported on ", sys.platform)
    return sourceclass
"""
