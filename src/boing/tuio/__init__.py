# -*- coding: utf-8 -*-
#
# boing/tuio/__init__.py -
#
# Author: Nicolas Roussel (nicolas.roussel@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

class TuioDescriptor(object):

    """Based on the TUIO 1.1 Protocol Specification
       http://www.tuio.org/?specification"""
    
    profiles = {
        "2Dobj":("s","i","x","y","a","X","Y","A","m","r"),
        "2Dcur":("s","x","y","X","Y","m"),
        "2Dblb":("s","x","y","a","w","h","f","X","Y","A","m","r"),
        "25Dobj":("s","i","x","y","z","a","X","Y","Z","A","m","r"),
        "25Dcur":("s","x","y","z","X","Y","Z","m"),
        "25Dblb":("s","x","y","z","a","w","h","f","X","Y","Z","A","m","r"),
        "3Dobj":("s","i","x","y","z","a","b","c","X","Y","Z","A","B","C","m","r"),
        "3Dcur":("s","x","y","z","X","Y","Z","m"),
        "3Dblb":("s","x","y","z","a","b","c","w","h","d","v","X","Y","Z","A","B","C","m","r"),
        }

    undef_value = -1.0


    def __init__(self, client,
                 profile, timetag, source, fseq,
                 *args):
        self.client = client
        self.profile = profile
        self.timetag = timetag
        self.source = source
        self.fseq = fseq
        names = TuioDescriptor.profiles[profile]
        if len(names)!=len(args):
            raise IndexError("""expecting "%s" for a %s"""%(names,profile))
        for name, arg in zip(names, args):
            self.__dict__[name] = arg

    def __str__(self):
        strings = [self.profile]
        for name in TuioDescriptor.profiles[self.profile]:
            strings.append("%s=%s"%(name,self.__dict__[name]))
        return " ".join(strings)

# -------------------------------------------------------------------

if __name__=="__main__":
    import datetime
    o = TuioDescriptor(None,
                       "2Dcur", datetime.datetime.now(), None, None,
                       "b232", 1, 2, 0, 22, 2)
    print(o)
