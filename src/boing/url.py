# -*- coding: utf-8 -*-
#
# boing/url.py -
#
# Authors: Nicolas Roussel (nicolas.roussel@inria.fr)
#          Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

"""
<draft-fielding-url-syntax-04> March 26, 1997

Uniform Resource Locators (URL): Generic Syntax and Semantics

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

# ---------------------------------------------------------------------

class URL_site(object):

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

# ---------------------------------------------------------------------

class URL_path(collections.UserList):

    def __init__(self, aString=''):
        if not aString:
            self.absolute = False
            self.data = []
        else:
            self.absolute = (aString[0]=='/')
            if self.absolute: aString = aString[1:]
            self.data = aString.split('/')
           
    def __str__(self):
        result = '/' if self.absolute else ''
        if self.data: result = result + '/'.join(self.data)
        if sys.platform=="win32" \
            and self.absolute \
            and os.path.splitdrive(result[1:])[0]:
            # instead of returning "/C:\\", return "C:\"
            result = result[1:]
        return result

# ---------------------------------------------------------------------

class URL_query(object):

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
        self.data = {}
        if aString:
            lst = aString.split('&')
            for kv in lst:
                tmp = kv.split('=')
                k = tmp[0]
                try: v = self._decode(tmp[1])
                except: v = ''
                self.data[k] = v

    def __repr__(self): return repr(self.data)
    def __cmp__(self, dict):
           if type(dict)==type(self.data):
               return cmp(self.data, dict)
           else:
               return cmp(self.data, dict.data)
    def __len__(self): return len(self.data)
    def __getitem__(self, key): return self.data[key]
    def __setitem__(self, key, item): self.data[key] = item
    def __delitem__(self, key): del self.data[key]

    def __str__(self):
        res = []
        for k,v in self.data.items():
            if v: res.append('%s=%s'%(self._encode(k),self._encode(v)))
            else: res.append(self._encode(k))
        return '&'.join(res)

    def keys(self): return self.data.keys()
    def items(self): return self.data.items()
    def values(self): return self.data.values()
    def has_key(self, key): return key in self.data  
    def get(self, key, default): return self.data.get(key, default)
    
# ---------------------------------------------------------------------

class URL(object):

    ABSOLUTE =   3
    RELATIVE =  28

    OPAQUE   =   1
    GENERIC  =   2
    NETPATH  =   4
    ABSPATH  =   8
    RELPATH  =  16

    generic = re.compile(
        '^'
        '([^:/?#]+)'      # scheme
        ':'
        '(.*)'            # relative url
        '$'
        )
    relative = re.compile(
        '^'
        '(//([^/?#]*))?' # site
        '([^?#]*)'       # path
        '(\?([^#]*))?'   # query string
        '(#(.*))?'       # fragment
        '$'
        )

    def __init__(self, aString=''):
        self.kind = 0
        self.scheme = ''
        self.opaque = ''
        self.site = URL_site('')
        self.path = URL_path('')
        self.query = URL_query('')
        self.fragment = ''
        if aString:
            m = URL.generic.match(aString)
            if m:
                self.scheme = m.group(1)
                self.kind = URL.GENERIC # Be optimistic
                aString = m.group(2)
            else:
                if aString[0:2]=='//':
                    self.kind = URL.NETPATH
                elif aString[0]=='/':
                    self.kind = URL.ABSPATH
                else:
                    self.kind = URL.RELPATH
            opaque = False
            try:
                m = URL.relative.match(aString)
                if m:
                    self.site = URL_site(m.group(2))
                    self.path = URL_path(m.group(3))
                    self.query = URL_query(m.group(5))
                    self.fragment = m.group(7)
                else:
                    opaque = True
            except:
                traceback.print_exc()
                opaque = True
            if opaque \
               or (self.kind==URL.GENERIC \
                   and self.path \
                   and (not self.path.absolute)):
                self.kind = URL.OPAQUE
                self.opaque = aString

    def __str__(self):
        result = ''
        if self.scheme: result += self.scheme + ':'
        if self.opaque: result += self.opaque
        else:
            site = str(self.site)
            if site:
                result += '//' + site
            result += str(self.path)
            query = str(self.query)
            if query: result += '?' + query
            if self.fragment: result += '#' + self.fragment
        return result

    def debug(self):
           kind = {
               3:'ABSOLUTE',
               1:'OPAQUE',
               2:'GENERIC',
               28:'RELATIVE',
               4:'NETPATH',
               8:'ABSPATH',
               16:'RELPATH'
               }
           print('KIND       :', kind[self.kind], end=' ')
           if self.kind&URL.ABSOLUTE: print ('(absolute)')
           elif self.kind&URL.RELATIVE: print ('(relative)')
           print()
           if self.kind&URL.ABSOLUTE:
               print('SCHEME     :', self.scheme)
               print()
           if self.kind&URL.OPAQUE:
               print('OPAQUE     :', self.opaque)
           else:
               print('SITE       :', self.site)
               print('  user     :', self.site.user)
               print('  password :', self.site.password)
               print('  host     :', self.site.host)
               print('  port     :', self.site.port)
               print('PATH       :', self.path)
               print('  data     :', self.path.data)
               print('QUERY      :', self.query)
               print('  data     :', self.query.data)
               print('FRAGMENT   :', self.fragment)

# ---------------------------------------------------------------------

UrlType = type(URL())

if __name__=="__main__":

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
        'udp6://[FF01:0:0:0:0:0:0:AA]:8888'
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
    
    if len(sys.argv)>1: tests = sys.argv[1:]
    else: tests = misc_tests+xmpp_tests
    for u in tests:
        print('-'*40)
        print(u)
        url = URL(u)
        print(url)
        print()
        url.debug()
        print()
