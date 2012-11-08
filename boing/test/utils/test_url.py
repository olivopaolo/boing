#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/utils/test_url.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import io
import itertools
import unittest

from boing.utils.url import URL

class TestURL(unittest.TestCase):

    def setUp(self):
        self.out = io.StringIO()

    def test_empty(self):
        string = ""
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.EMPTY)
        self.assertFalse(url.kind&URL.ABSOLUTE)
        self.assertFalse(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "")
        self.assertFalse(url.path)
        self.assertEqual(url.path.data, tuple())
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertFalse(url.query)
        self.assertEqual(dict(url.query.items()), {})
        # fragment
        self.assertEqual(url.fragment, "")
        self.assertFalse(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_generic_full(self):
        string = "scheme://user:password@host:1212/first/second?k1=v1&k2=v2#frag"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.GENERIC)
        self.assertTrue(url.kind&URL.ABSOLUTE)
        self.assertFalse(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "scheme")
        # site
        self.assertEqual(url.site, "user:password@host:1212")
        self.assertTrue(url.site)
        self.assertEqual(url.site.user, "user")
        self.assertEqual(url.site.password, "password")
        self.assertEqual(url.site.host, "host")
        self.assertEqual(url.site.port, 1212)
        # path
        self.assertEqual(url.path, "/first/second")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, ("first", "second"))
        self.assertTrue(url.path.isAbsolute())
        # query
        self.assertTrue(url.query)
        self.assertEqual(dict(url.query.items()), {"k1": "v1", "k2": "v2"})
        # fragment
        self.assertEqual(url.fragment, "frag")
        self.assertTrue(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_generic_min(self):
        string = ":"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.GENERIC)
        self.assertTrue(url.kind&URL.ABSOLUTE)
        self.assertFalse(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "")
        self.assertFalse(url.path)
        self.assertEqual(url.path.data, tuple())
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertFalse(url.query)
        self.assertEqual(dict(url.query.items()), {})
        # fragment
        self.assertEqual(url.fragment, "")
        self.assertFalse(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_generic_IPv6(self):
        string = "scheme://[FF01:0:0:0:0:0:0:AA]:8888"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.GENERIC)
        self.assertTrue(url.kind&URL.ABSOLUTE)
        self.assertFalse(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "scheme")
        # site
        self.assertEqual(url.site, "[FF01:0:0:0:0:0:0:AA]:8888")
        self.assertTrue(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "FF01:0:0:0:0:0:0:AA")
        self.assertEqual(url.site.port, 8888)
        # path
        self.assertEqual(url.path, "")
        self.assertFalse(url.path)
        self.assertEqual(url.path.data, tuple())
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertFalse(url.query)
        self.assertEqual(dict(url.query.items()), {})
        # fragment
        self.assertEqual(url.fragment, "")
        self.assertFalse(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_netpath_full(self):
        string = "//user:password@host:1212/first/second?k1=v1&k2=v2#frag"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.NETPATH)
        self.assertFalse(url.kind&URL.ABSOLUTE)
        self.assertTrue(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "user:password@host:1212")
        self.assertTrue(url.site)
        self.assertEqual(url.site.user, "user")
        self.assertEqual(url.site.password, "password")
        self.assertEqual(url.site.host, "host")
        self.assertEqual(url.site.port, 1212)
        # path
        self.assertEqual(url.path, "/first/second")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, ("first", "second"))
        self.assertTrue(url.path.isAbsolute())
        # query
        self.assertTrue(url.query)
        self.assertEqual(dict(url.query.items()), {"k1": "v1", "k2": "v2"})
        # fragment
        self.assertEqual(url.fragment, "frag")
        self.assertTrue(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_netpath_min(self):
        string = "//"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.NETPATH)
        self.assertFalse(url.kind&URL.ABSOLUTE)
        self.assertTrue(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "")
        self.assertFalse(url.path)
        self.assertEqual(url.path.data, tuple())
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertFalse(url.query)
        self.assertEqual(dict(url.query.items()), {})
        # fragment
        self.assertEqual(url.fragment, "")
        self.assertFalse(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_absolutepath_full(self):
        string = "/first/second?k1=v1&k2=v2#frag"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.ABSPATH)
        self.assertFalse(url.kind&URL.ABSOLUTE)
        self.assertTrue(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "/first/second")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, ("first", "second"))
        self.assertTrue(url.path.isAbsolute())
        # query
        self.assertTrue(url.query)
        self.assertEqual(dict(url.query.items()), {"k1": "v1", "k2": "v2"})
        # fragment
        self.assertEqual(url.fragment, "frag")
        self.assertTrue(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_absolutepath_min(self):
        string = "/"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.ABSPATH)
        self.assertFalse(url.kind&URL.ABSOLUTE)
        self.assertTrue(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "/")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, ("", ))
        self.assertTrue(url.path.isAbsolute())
        # query
        self.assertFalse(url.query)
        self.assertEqual(dict(url.query.items()), {})
        # fragment
        self.assertEqual(url.fragment, "")
        self.assertFalse(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_relativepath_full(self):
        string = "first?k1=v1&k2=v2#frag"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.RELPATH)
        self.assertFalse(url.kind&URL.ABSOLUTE)
        self.assertTrue(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "first")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, ("first", ))
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertTrue(url.query)
        self.assertEqual(dict(url.query.items()), {"k1": "v1", "k2": "v2"})
        # fragment
        self.assertEqual(url.fragment, "frag")
        self.assertTrue(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_relativepath_min(self):
        string = "first"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.RELPATH)
        self.assertFalse(url.kind&URL.ABSOLUTE)
        self.assertTrue(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "first")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, ("first", ))
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertFalse(url.query)
        self.assertEqual(dict(url.query.items()), {})
        # fragment
        self.assertEqual(url.fragment, "")
        self.assertFalse(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_relativepath_dotted_full(self):
        string = "./first?k1=v1&k2=v2#frag"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.RELPATH)
        self.assertFalse(url.kind&URL.ABSOLUTE)
        self.assertTrue(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "./first")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, (".", "first"))
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertTrue(url.query)
        self.assertEqual(dict(url.query.items()), {"k1": "v1", "k2": "v2"})
        # fragment
        self.assertEqual(url.fragment, "frag")
        self.assertTrue(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_relativepath_dotted_min(self):
        string = "./first?k1=v1&k2=v2#frag"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.RELPATH)
        self.assertFalse(url.kind&URL.ABSOLUTE)
        self.assertTrue(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "./first")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, (".", "first"))
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertTrue(url.query)
        self.assertEqual(dict(url.query.items()), {"k1": "v1", "k2": "v2"})
        # fragment
        self.assertEqual(url.fragment, "frag")
        self.assertTrue(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_opaque_full(self):
        string = "mailto:user@host.domain?k1=v1&k2=v2#frag"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.OPAQUE)
        self.assertTrue(url.kind&URL.ABSOLUTE)
        self.assertFalse(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "mailto")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "user@host.domain")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, ("user@host.domain", ))
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertTrue(url.query)
        self.assertEqual(dict(url.query.items()), {"k1": "v1", "k2": "v2"})
        # fragment
        self.assertEqual(url.fragment, "frag")
        self.assertTrue(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "user@host.domain?k1=v1&k2=v2#frag")
        self.assertTrue(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_opaque_min(self):
        string = ":opaque"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.OPAQUE)
        self.assertTrue(url.kind&URL.ABSOLUTE)
        self.assertFalse(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "opaque")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, ("opaque", ))
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertFalse(url.query)
        self.assertEqual(dict(url.query.items()), {})
        # fragment
        self.assertEqual(url.fragment, "")
        self.assertFalse(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "opaque")
        self.assertTrue(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_not_opaque(self):
        string = ":/"
        url = URL(string)
        self.assertEqual(url, ":///")
        # kind
        self.assertEqual(url.kind, URL.GENERIC)
        self.assertTrue(url.kind&URL.ABSOLUTE)
        self.assertFalse(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "/")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, ("", ))
        self.assertTrue(url.path.isAbsolute())
        # query
        self.assertFalse(url.query)
        self.assertEqual(dict(url.query.items()), {})
        # fragment
        self.assertEqual(url.fragment, "")
        self.assertFalse(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_not_opaque_2(self):
        string = ":./first"
        url = URL(string)
        self.assertEqual(url, string)
        # kind
        self.assertEqual(url.kind, URL.GENERIC)
        self.assertTrue(url.kind&URL.ABSOLUTE)
        self.assertFalse(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "")
        # site
        self.assertEqual(url.site, "")
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "./first")
        self.assertTrue(url.path)
        self.assertEqual(url.path.data, (".", "first"))
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertFalse(url.query)
        self.assertEqual(dict(url.query.items()), {})
        # fragment
        self.assertEqual(url.fragment, "")
        self.assertFalse(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_percent_encoded_string(self):
        string = "udp://:8888?prénom=Jérémie"
        url = URL(string)
        self.assertEqual(url, "udp://:8888?pr%e9nom=J%e9r%e9mie")
        # kind
        self.assertEqual(url.kind, URL.GENERIC)
        self.assertTrue(url.kind&URL.ABSOLUTE)
        self.assertFalse(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "udp")
        # site
        self.assertEqual(url.site, ":8888")
        self.assertTrue(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 8888)
        # path
        self.assertEqual(url.path, "")
        self.assertFalse(url.path)
        self.assertEqual(url.path.data, tuple())
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertTrue(url.query)
        self.assertEqual(dict(url.query.items()), {"prénom": "Jérémie"})
        # fragment
        self.assertEqual(url.fragment, "")
        self.assertFalse(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

    def test_replacement_tag(self):
        string = "nop:?<!asd=asd?3esxc!>=1&k2=<!1^&$DF!CV?!>"
        url = URL(string)
        self.assertEqual(url,
                         "nop:?asd%3dasd%3f3esxc=1&k2=1%5e%26%24DF%21CV%3f")
        # kind
        self.assertEqual(url.kind, URL.GENERIC)
        self.assertTrue(url.kind&URL.ABSOLUTE)
        self.assertFalse(url.kind&URL.RELATIVE)
        # scheme
        self.assertEqual(url.scheme, "nop")
        # site
        self.assertFalse(url.site)
        self.assertEqual(url.site.user, "")
        self.assertEqual(url.site.password, "")
        self.assertEqual(url.site.host, "")
        self.assertEqual(url.site.port, 0)
        # path
        self.assertEqual(url.path, "")
        self.assertFalse(url.path)
        self.assertEqual(url.path.data, tuple())
        self.assertFalse(url.path.isAbsolute())
        # query
        self.assertTrue(url.query)
        self.assertEqual(dict(url.query.items()),
                         {"asd=asd?3esxc": "1",
                          "k2": "1^&$DF!CV?"})
        # fragment
        self.assertEqual(url.fragment, "")
        self.assertFalse(url.fragment)
        # opaque
        self.assertEqual(url.opaque, "")
        self.assertFalse(url.opaque)
        # str
        str(url)
        # debug
        url.debug(self.out)

# -------------------------------------------------------------------

def suite():
    testcases = (
        TestURL,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == "__main__":
    unittest.TextTestRunner().run(suite())
