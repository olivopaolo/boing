# -*- coding: utf-8 -*-
#
# boing/utils/url.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""
Uniform Resource Locators (URL): Generic Syntax and Semantics

<draft-fielding-url-syntax-04> March 26, 1997

T. Berners-Lee (MIT/LCS)
R. Fielding (U.C. Irvine)
L. Masinter (Xerox Corporation)
"""

import collections
import sys
import os.path
import re
import string
import traceback

class URL:

    ABSOLUTE  =   3
    RELATIVE =  28

    EMPTY =      0
    OPAQUE   =   1
    GENERIC  =   2
    NETPATH  =   4
    ABSPATH  =   8
    RELPATH  =  16

    _generic = re.compile(
        '^'
        '([^:/?#]*)'      # scheme
        ':'
        '(.*)'            # relative url
        '$'
        )
    _relative = re.compile(
        '^'
        '(//([^/?#]*))?' # site
        '([^?#]*)'       # path
        '(\?([^#]*))?'   # query string
        '(#(.*))?'       # fragment
        '$'
        )

    def __init__(self, aString=''):
        self._kind = URL.EMPTY
        self._scheme = ''
        self._site = URL_site('')
        self._path = URL_path('')
        self.query = URL_query('')
        self._fragment = ''
        if aString:
            aString.replace("\\", "/") # Windows path to Unix path
            m = URL._generic.match(aString)
            if m:
                self._scheme = m.group(1)
                self._kind = URL.GENERIC # Be optimistic
                aString = m.group(2)
            else:
                if aString[0:2]=='//':
                    self._kind = URL.NETPATH
                elif aString[0]=='/':
                    self._kind = URL.ABSPATH
                else:
                    self._kind = URL.RELPATH
            opaque = False
            try:
                m = URL._relative.match(aString)
                if m:
                    self._site = URL_site(m.group(2))
                    self._path = URL_path(m.group(3))
                    self.query = URL_query(m.group(5))
                    self._fragment = "" if m.group(7) is None else m.group(7)
                else:
                    opaque = True
            except:
                traceback.print_exc()
                opaque = True
            if opaque or \
                    self.kind==URL.GENERIC and self.path \
                    and not self.path.isAbsolute() \
                    and not self.path.data[0]==".":
                self._kind = URL.OPAQUE
                # self.opaque = aString
                # self._path = URL_path('')
                # self.query = URL_query('')

    @property
    def kind(self): return self._kind
    @property
    def scheme(self): return self._scheme
    @property
    def site(self): return self._site
    @property
    def path(self): return self._path
    @property
    def fragment(self): return self._fragment

    @property
    def opaque(self):
        if self.kind!=URL.OPAQUE: rvalue = str()
        else:
            rvalue = str(self.path)
            query = str(self.query)
            if query: rvalue += '?' + query
            if self.fragment: rvalue += '#' + self.fragment
        return rvalue

    def __add__(self, other):
        return str(self)+other if isinstance(other, str) \
            else NotImplemented

    def __radd__(self, other):
        return other+str(self) if isinstance(other, str) \
            else NotImplemented

    def __repr__(self):
        return "URL('%s')"%str(self)

    def __str__(self):
        result = ''
        if self.scheme or self.kind==URL.OPAQUE or self.kind&URL.ABSOLUTE:
            result += self.scheme + ':'
        if self.kind==URL.OPAQUE: result += self.opaque
        else:
            site = str(self.site)
            if site \
                    or self.kind&URL.NETPATH \
                    or self.kind&URL.ABSOLUTE and self.path.isAbsolute():
                result += '//' + site
            result += str(self.path)
            query = str(self.query)
            if query: result += '?' + query
            if self.fragment: result += '#' + self.fragment
        return result

    def __copy__(self):
        return URL(str(self))

    def __deepcopy__(self, *args, **kwargs):
        return URL(str(self))

    def debug(self, fd=sys.stdout):
        kind = {
            0:'EMPTY',
            3:'ABSOLUTE',
            1:'OPAQUE',
            2:'GENERIC',
            28:'RELATIVE',
            4:'NETPATH',
            8:'ABSPATH',
            16:'RELPATH'
            }
        print('KIND       :', kind[self.kind], end=' ', file=fd)
        if self.kind&URL.ABSOLUTE: print ('(absolute)', file=fd)
        elif self.kind&URL.RELATIVE: print ('(relative)', file=fd)
        print(file=fd)
        if self.kind&URL.ABSOLUTE:
            print('SCHEME     :', self.scheme, file=fd)
            print(file=fd)
        if self.kind&URL.OPAQUE:
            print('OPAQUE     :', self.opaque, file=fd)
            print(file=fd)
        print('SITE       :', self.site, file=fd)
        print('  user     :', self._site.user, file=fd)
        print('  password :', self._site.password, file=fd)
        print('  host     :', self._site.host, file=fd)
        print('  port     :', self._site.port, file=fd)
        print('PATH       :', self.path, file=fd)
        print('  data     :', self.path.data, file=fd)
        print('QUERY      :', self.query, file=fd)
        print('  data     :', self.query._data, file=fd)
        print('FRAGMENT   :', self.fragment, file=fd)

    def __eq__(self, other):
        return str(self)==str(other)

    def __ne__(self, other):
        return str(self)!=str(other)

# ---------------------------------------------------------------------

class URL_site:

    def __init__(self, aString=''):
        if not aString:
            self.user = ''
            self.password = ''
            self.host = ''
            self.port = 0
        else:
            tmp = aString.split('@')
            if len(tmp)==1:
                userpass, hostport = '', aString
            elif len(tmp)==2:
                userpass, hostport = tmp[0], tmp[1]
            else: raise TypeError
            tmp = userpass.split(':')
            if len(tmp)==1:
                self.user, self.password = userpass, ''
            elif len(tmp)==2:
                self.user, self.password = tmp[0], tmp[1]
            else: raise TypeError
            if hostport[0]=='[':
                p = hostport.find(']')
                if p==-1: raise TypeError
                self.host = hostport[1:p]
                tmp = hostport[p+1:]
                if len(tmp)>1 and tmp[0]==':':
                    self.port = int(tmp[1:])
                else: self.port = 0
            else:
                tmp = hostport.split(':')
                if len(tmp)==1:
                    self.host, self.port = hostport, 0
                elif len(tmp)==2:
                    self.host, self.port = tmp[0], int(tmp[1])
                else: raise TypeError

    def __repr__(self):
        return "URL_site('%s')"%str(self)

    def __str__(self):
        result = ''
        if self.user:
            result = result + self.user
            if self.password: result = result + ':' + self.password
            result = result + '@'
        if self.host.find(':')!=-1:
            result = result + '[' + self.host + ']'
        else: result = result + self.host
        if self.port: result = result + ':' + str(self.port)
        return result

    def __bool__(self):
        return bool(self.host) or self.port!=0 \
            or bool(self.user) or bool(self.password)

    def __eq__(self, other):
        return str(self)==str(other)

    def __ne__(self, other):
        return str(self)!=str(other)

# ---------------------------------------------------------------------

class URL_path(collections.UserList):

    def __init__(self, aString=''):
        if not aString:
            self._absolute = False
            self.data = tuple()
        else:
            self._absolute = (aString[0]=='/')
            if self.isAbsolute(): aString = aString[1:]
            self.data = tuple(aString.split('/'))

    def isAbsolute(self):
        """Return wheter the path is absolute."""
        return self._absolute

    def __repr__(self):
        return "URL_path('%s')"%str(self)

    def __str__(self):
        result = '/' if self.isAbsolute() else ''
        if self.data: result = result + '/'.join(self.data)
        # if sys.platform=="win32" \
        #     and self.isAbsolute() \
        #     and os.path.splitdrive(result[1:])[0]:
        #     # instead of returning "/C:\\", return "C:\"
        #     result = result[1:]
        return result

    def __bool__(self):
        return self.isAbsolute() or bool(self.data)

    def __eq__(self, other):
        return str(self)==str(other)

    def __ne__(self, other):
        return str(self)!=str(other)

# ---------------------------------------------------------------------

class URL_query(collections.MutableMapping):

    def _encode(self, text):
        res = ''
        for c in text:
            o = ord(c)
            if c==' ':
                res = res+'+'
            elif (c in """%+&=#;/?:$!,'()<>\"\t\\^{}[]`|~""") \
              or (0<=o<=31) or (o>=127) :
                res = res+'%%%02x'%o
            else:
                res = res+c
        return res

    def _decode(self, text):
        res, begin = '', 0
        while 1:
            end = text[begin:].find('%')
            if end<0: break
            end = begin+end
            res = res+text[begin:end]
            v = int(text[end+1:end+3],16)
            res = res+chr(v)
            begin = end+3
        res = res+text[begin:]
        return re.sub('\+',' ',res)

    # ---------------------------------------------------------------

    def __init__(self, aString=''):
        self._data = collections.OrderedDict()
        if aString:

            innerurl = re.compile("=['\"].*?['\"]")
            innertag = re.compile("<\[!#([0-9]+)\]>")
            sub = []
            def encode_inner(match):
                m = match.group()
                sub.append(match.group()[2:-1])
                return "=<[!#%d]>"%(len(sub)-1)
            def decode_inner(match):
                return sub.pop(0)

            aString = innerurl.sub(encode_inner, aString)
            lst = aString.split('&')
            for kv in lst:
                tmp = kv.split('=', 1)
                k = tmp[0]
                value = innertag.sub(decode_inner, tmp[1]) if len(tmp)>1 \
                    else ""
                try: v = self._decode(value)
                except: v = ''
                self._data[k] = v

    def __repr__(self): return "URL_query('%s')"%str(self)
    def __cmp__(self, dict):
           if type(dict)==type(self._data):
               return cmp(self._data, dict)
           else:
               return cmp(self._data, dict.data)
    def __len__(self): return len(self._data)
    def __getitem__(self, key): return self._data[key]
    def __setitem__(self, key, item): self._data[key] = item
    def __delitem__(self, key): del self._data[key]
    def __contains__(self, key): return key in self._data
    def __iter__(self): return iter(self._data)

    def __str__(self):
        res = []
        for k,v in self._data.items():
            if v: res.append('%s=%s'%(self._encode(k),self._encode(v)))
            else: res.append(self._encode(k))
        return '&'.join(res)

# ---------------------------------------------------------------------

if __name__=="__main__":
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ('help',))
    except getopt.GetoptError as err:
        print(err)
        print("usage: %s [urls]"%sys.argv[0])
        print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
        sys.exit(2)
    for o, a in opts:
        if o in ("-h", "--help"):
            print("usage: %s <urls>"%sys.argv[0])
            print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
            print("""
    Print debug details for argument URLs.

    Options:
     -h, --help                  display this help and exit
      """)
            sys.exit(0)

    misc_tests = [
        'http://user:password@host:1212/path1/path2?query1=query2#frag',
        '/first/second?user=firstname+lastname&host=somehost&time=now',
        '//user@host/toto/tutu',
        '/pub/python',
        'index.html',
        '/',
        '?titi=toto',
        'http://:8001',
        'mailto:user@host.domain',
        'mcast://225.0.0.250:8123',
        'mcast://<broadcast>:8080',
        'udp6://[FF01:0:0:0:0:0:0:AA]:8888',
        'file:///tmp/file.tmp',
        ]

    xmpp_tests = [
        # --------------------------
        'xmpp:example.com', # identifies a server
        'xmpp:example-node@example.com', # identifies a server
        'xmpp:example-node@example.com/some-resource', # identifies a node
        'xmpp:support@example.com?message;subject=Hello%20World', # compose a message to "support"
        # --------------------------
        'xmpp://guest@example.com', # authenticate as "guest@example.com"
        'xmpp://guest@example.com/support@example.com?message', # authenticate then compose a message to "support"
        # --------------------------
        'xmpp-component://plays@shakespeare.lit',
        ]

    boing_tests = [

        "out.tuio.service:name",
        "out.tuio.tcp://host:9898",
        "out:/tmp/toto.osc",
        "out:stdout?asd=12",
        "in:./file.txt?q1=v1",
        "in.tuio.tcp://:9898", # empty host or localhost or 127.0.0.1 or ::1
        ]

    if len(sys.argv)>1: tests = sys.argv[1:]
    else: tests = misc_tests + boing_tests +xmpp_tests
    for u in tests:
        print('-'*40)
        print(u)
        url = URL(u)
        print(url)
        print()
        url.debug()
        print()
