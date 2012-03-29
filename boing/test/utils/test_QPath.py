#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/utils/test_QPath.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import unittest

import boing.utils.QPath as QPath

class Test_QPath(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.obj = {"store": {
                "book": [ 
                    { "category": "reference",
                      "author": "Nigel Rees",
                      "title": "Sayings of the Century",
                      "price": 8.95
                      },
                    { "category": "fiction",
                      "author": "Evelyn Waugh",
                      "title": "Sword of Honour",
                      "price": 12.99
                      },
                    { "category": "fiction",
                      "author": "Herman Melville",
                      "title": "Moby Dick",
                      "isbn": "0-553-21311-3",
                      "price": 8.99
                      },
                    { "category": "fiction",
                      "author": "J. R. R. Tolkien",
                      "title": "The Lord of the Rings",
                      "isbn": "0-395-19395-8",
                      "price": 22.99
                      }
                    ],
                "bicycle": { 
                    "color": "red",
                    "price": 19.95
                    }
                }
                    }

    def test_None_get(self):
        path = None
        self.assertRaises(TypeError, QPath.get, self.obj, path)

    def test_None_filter(self):
        path = None
        self.assertRaises(TypeError, QPath.get, self.obj, path)

    def test_None_test(self):
        path = None
        self.assertRaises(TypeError, QPath.get, self.obj, path)

    def test_empty_get(self):
        path = ""
        self.assertEqual(QPath.get(self.obj, path),
                         [self.obj])

    def test_empty_filter(self):
        path = ""
        self.assertEqual(QPath.filter(self.obj, path),
                         self.obj)

    def test_empty_test(self):
        path = ""
        self.assertTrue(QPath.test(self.obj, path))

    def test_relative_get(self):
        path = "store.bicycle"
        self.assertEqual(QPath.get(self.obj, path),
                         [{'color': 'red', 'price': 19.95}])

    def test_relative_filter(self):
        path = "store.bicycle"
        self.assertEqual(QPath.filter(self.obj, path),
                         {'store':{'bicycle':{'color':'red','price': 19.95}}})

    def test_relative_test(self):
        path = "store.bicycle"
        self.assertTrue(QPath.test(self.obj, path))

    def test_absolute_get(self):
        for path in ("$.store.bicycle", 
                     "$['store']['bicycle']"):
            self.assertEqual(QPath.get(self.obj, path),
                             [{'color': 'red', 'price': 19.95}])

    def test_absolute_filter(self):
        for path in ("$.store.bicycle",
                     "$['store']['bicycle']"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'bicycle':{'color':'red','price': 19.95}}})

    def test_absolute_test(self):
        for path in ("$.store.bicycle", 
                     "$['store']['bicycle']"):
            self.assertTrue(QPath.test(self.obj, path))

    def test_numeric_get(self):
        for path in ("$.store.book.0.author", 
                     "$.store.book[0].author", 
                     "$['store']['book'][0]['author']"):
            self.assertEqual(QPath.get(self.obj, path),
                             ['Nigel Rees'])

    def test_numeric_filter(self):
        for path in ("$.store.book.0.author", 
                     "$.store.book[0].author", 
                     "$['store']['book'][0]['author']"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'author':'Nigel Rees'}]}})

    def test_numeric_test(self):
        for path in ("$.store.book.0.author", 
                     "$.store.book[0].author", 
                     "$['store']['book'][0]['author']"):
            self.assertTrue(QPath.test(self.obj, path))

    def test_empty_result_get(self):
        for path in ("folder",
                     "$.folder",
                     "$[folder]",
                     "store.book.7"):
            self.assertEqual(QPath.get(self.obj, path),[])

    def test_empty_result_filter(self):
        for path in ("folder",
                     "$.folder",
                     "$[folder]",
                     "store.book.7"):
            self.assertEqual(QPath.filter(self.obj, path), None)

    def test_empty_result_test(self):
        for path in ("folder",
                     "$.folder",
                     "$[folder]",
                     "store.book.7"):
            self.assertFalse(QPath.test(self.obj, path))

    def test_wildcard_get(self):
        for path in ("$.store.book.*.price",
                     "$['store']['book'][*]['price']",
                     "$['store']['book']['*']['price']"):
            self.assertEqual(QPath.get(self.obj, path),
                             [8.95, 12.99, 8.99, 22.99])

    def test_wildcard_filter(self):
        for path in ("$.store.book.*.price",
                     "$['store']['book'][*]['price']",
                     "$['store']['book']['*']['price']"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'price':8.95},
                                               {'price':12.99},
                                               {'price':8.99},
                                               {'price':22.99}]}})

    def test_wildcard_test(self):
        for path in ("$.store.book.*.price",
                     "$['store']['book'][*]['price']",
                     "$['store']['book']['*']['price']"):
            self.assertTrue(QPath.get(self.obj, path))

    def test_fullslice_get(self):
        for path in ("$.store.book[:].price",
                     "$['store']['book'][':']['price']",
                     "$['store']['book'][:]['price']"):
            self.assertEqual(QPath.get(self.obj, path),
                             [8.95, 12.99, 8.99, 22.99])

    def test_fullslice_filter(self):
        for path in ("$.store.book[:].price",
                     "$['store']['book'][':']['price']",
                     "$['store']['book'][:]['price']"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'price':8.95},
                                               {'price':12.99},
                                               {'price':8.99},
                                               {'price':22.99}]}})

    def test_fullslice_test(self):
        for path in ("$.store.book[:].price",
                     "$['store']['book'][':']['price']",
                     "$['store']['book'][:]['price']"):
            self.assertTrue(QPath.test(self.obj, path))

    def test_slice_begin_get(self):
        for path in ("$.store.book[2:].price",
                     "$['store']['book']['2:']['price']",
                     "$['store']['book'][2:]['price']"):
            self.assertEqual(QPath.get(self.obj, path),
                             [8.99, 22.99])

    def test_slice_begin_filter(self):
        for path in ("$.store.book[2:].price",
                     "$['store']['book']['2:']['price']",
                     "$['store']['book'][2:]['price']"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'price':8.99},
                                               {'price':22.99}]}})

    def test_slice_begin_test(self):
        for path in ("$.store.book[2:].price",
                     "$['store']['book']['2:']['price']",
                     "$['store']['book'][2:]['price']"):
            self.assertTrue(QPath.get(self.obj, path))

    def test_slice_end_get(self):
        for path in ("$.store.book[:-1].price",
                     "$['store']['book'][':-1']['price']",
                     "$['store']['book'][:-1]['price']"):
            self.assertEqual(QPath.get(self.obj, path),
                             [8.95, 12.99, 8.99])

    def test_slice_end_filter(self):
        for path in ("$.store.book[:-1].price",
                     "$['store']['book'][':-1']['price']",
                     "$['store']['book'][:-1]['price']"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'price':8.95},
                                               {'price':12.99},
                                               {'price':8.99}]}})

    def test_slice_end_test(self):
        for path in ("$.store.book[:-1].price",
                     "$['store']['book'][':-1']['price']",
                     "$['store']['book'][:-1]['price']"):
            self.assertTrue(QPath.test(self.obj, path))

    def test_slice_step_get(self):
        for path in ("$.store.book[::2].price",
                     "$['store']['book']['::2']['price']",
                     "$['store']['book'][::2]['price']"):
            self.assertEqual(QPath.get(self.obj, path),
                             [8.95, 8.99])

    def test_slice_step_filter(self):
        for path in ("$.store.book[::2].price",
                     "$['store']['book']['::2']['price']",
                     "$['store']['book'][::2]['price']"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'price':8.95},
                                               {'price':8.99}]}})

    def test_slice_step_test(self):
        for path in ("$.store.book[::2].price",
                     "$['store']['book']['::2']['price']",
                     "$['store']['book'][::2]['price']"):
            self.assertTrue(QPath.test(self.obj, path))

    def test_recursive_descent_get(self):
        for path in ("$.store..price", 
                     "$['store']..['price']",
                     "$..price"):
            self.assertEqual(QPath.get(self.obj, path),
                             [8.95, 12.99, 8.99, 22.99, 19.95])

    def test_recursive_descent_filter(self):
        for path in ("$.store..price", 
                     "$['store']..['price']",
                     "$..price"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'price':8.95},
                                               {'price':12.99},
                                               {'price':8.99},
                                               {'price':22.99}],
                                       'bicycle':{'price':19.95}}})

    def test_recursive_descent_test(self):
        for path in ("$.store..price", 
                     "$['store']..['price']",
                     "$..price"):
            self.assertTrue(QPath.get(self.obj, path))

    def test_comma_union_get(self):
        for path in ("$.store.book,bicycle,car..price",
                     "$['store']['book,bicycle']..['price']"):
            self.assertEqual(QPath.get(self.obj, path),
                             [8.95, 12.99, 8.99, 22.99, 19.95])

    def test_comma_union_filter(self):
        for path in ("$.store.book,bicycle,car..price",
                     "$['store']['book,bicycle']..['price']"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'price':8.95},
                                               {'price':12.99},
                                               {'price':8.99},
                                               {'price':22.99}],
                                       'bicycle':{'price':19.95}}})

    def test_comma_union_test(self):
        for path in ("$.store.book,bicycle,car..price",
                     "$['store']['book,bicycle']..['price']"):
            self.assertTrue(QPath.get(self.obj, path))

    def test_pipe_union_get(self):
        for path in ("$..book.*.price|$..bicycle.color",
                     "$..book.*.price |$..bicycle.color",
                     "$..book.*.price| $..bicycle.color",
                     "$..book.*.price | $..bicycle.color",
                     "store.book.*.price|store.bicycle.color"):
            self.assertEqual(QPath.get(self.obj, path),
                             [8.95, 12.99, 8.99, 22.99, 'red'])

    def test_pipe_union_filter(self):
        for path in ("$..book.*.price|$..bicycle.color",
                     "$..book.*.price |$..bicycle.color",
                     "$..book.*.price| $..bicycle.color",
                     "$..book.*.price | $..bicycle.color",
                     "store.book.*.price|store.bicycle.color"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'price':8.95},
                                               {'price':12.99},
                                               {'price':8.99},
                                               {'price':22.99}],
                                       'bicycle':{'color':'red'}}})

    def test_pipe_union_test(self):
        for path in ("$..book.*.price|$..bicycle.color",
                     "$..book.*.price |$..bicycle.color",
                     "$..book.*.price| $..bicycle.color",
                     "$..book.*.price | $..bicycle.color",
                     "store.book.*.price|store.bicycle.color"):
            self.assertTrue(QPath.test(self.obj, path))

    def test_script_index_get(self):
        for path in ("$..book[(@.__len__()-1)]",
                     "$..['book'][(@.__len__()-1)]"):
            self.assertEqual(QPath.get(self.obj, path),
                             [{'category': 'fiction', 'price': 22.99, 
                               'title': 'The Lord of the Rings', 
                               'isbn': '0-395-19395-8', 
                               'author': 'J. R. R. Tolkien'}])

    def test_script_index_filter(self):
        for path in ("$..book[(@.__len__()-1)]",
                     "$..['book'][(@.__len__()-1)]"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'category': 'fiction', 
                                                'price': 22.99, 
                                                'title': 'The Lord of the Rings', 
                                                'isbn': '0-395-19395-8', 
                                                'author': 'J. R. R. Tolkien'}]}})

    def test_script_index_test(self):
        for path in ("$..book[(@.__len__()-1)]",
                     "$..['book'][(@.__len__()-1)]"):
            self.assertTrue(QPath.get(self.obj, path))

    def test_script_query_get(self):
        for path in ("$..book[?(@['price']<10)].title",
                     "$..book[?(@['price']<10)].title"):
            self.assertEqual(QPath.get(self.obj, path),
                             ['Sayings of the Century', 'Moby Dick'])

    def test_script_query_filter(self):
        for path in ("$..book[?(@['price']<10)].title",
                     "$..book[?(@['price']<10)].title"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'title':'Sayings of the Century'},
                                               {'title':'Moby Dick'}]}})

    def test_script_query_test(self):
        for path in ("$..book[?(@['price']<10)].title",
                     "$..book[?(@['price']<10)].title"):
            self.assertTrue(QPath.test(self.obj, path))

    def test_script_query2_get(self):
        for path in ("$..book[?(@['isbn'])].title",
                     "$..book[?(@['isbn'])].title"):
            self.assertEqual(QPath.get(self.obj, path),
                             ['Moby Dick', 'The Lord of the Rings'])

    def test_script_query2_filter(self):
        for path in ("$..book[?(@['isbn'])].title",
                     "$..book[?(@['isbn'])].title"):
            self.assertEqual(QPath.filter(self.obj, path),
                             {'store':{'book':[{'title':'Moby Dick'},
                                               {'title':'The Lord of the Rings'}]}})

    def test_script_query2_test(self):
        for path in ("$..book[?(@['isbn'])].title",
                     "$..book[?(@['isbn'])].title"):
            self.assertTrue(QPath.get(self.obj, path))

# -------------------------------------------------------------------

def suite():    
    tests = (t for t in Test_QPath.__dict__ if t.startswith("test_"))
    return unittest.TestSuite(map(Test_QPath, tests))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
