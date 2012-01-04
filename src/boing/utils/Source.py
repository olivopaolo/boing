# -*- coding: utf-8 -*-
#
# boing/utils/Source.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import sys
import traceback

from boing.json.JSONTunnel import JSONReader
from boing.tuio.TuioToState import TuioSource
from boing.url import URL

if sys.platform=='linux2':
    from boing.multitouch.MtDevDevice import MtDevDevice

def Source(url):
    """Create a new event source instance using the argument "url"."""
    if not isinstance(url, URL): url = URL(str(url))
    source = None
    if url.kind in (URL.ABSPATH, URL.RELPATH) \
            or url.scheme.startswith("tuio"): 
        source = TuioSource(url)
    elif url.scheme.startswith("json"):
        source = JSONReader(url)
    elif url.scheme.startswith("mtdev"):
        if sys.platform == "linux2":
            try:
                source = MtDevDevice(str(url.path))
            except Exception:
                traceback.print_exc()
        else:
            print("mtdev devices are not supported on ", sys.platform)
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
