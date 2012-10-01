#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# boing/test/utils/test_querypath.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import itertools
import unittest

from  boing.utils import querypath
QPath = querypath.QPath


class Test_QPath(unittest.TestCase):

    def test_None(self):
        self.assertRaises(TypeError, QPath, None)

    def test_empty_string(self):
        QPath("")

    def test_str(self):
        self.assertEqual(str(QPath("store")), "store")

    def test_hash(self):
        self.assertEqual(hash(QPath("store")), hash("store"))

    def test_bool(self):
        self.assertFalse(bool(QPath("")))
        self.assertTrue(bool(QPath("store")))

    def test_eq_same(self):
        self.assertEqual(QPath(""), QPath(""))

    def test_eq_pipe_equivalent(self):
        q1 = QPath("store|..color")
        q2 = QPath("..color|store")
        self.assertEqual(q1, q2)

    def test_ne(self):
        self.assertNotEqual(QPath("store"), QPath(""))

    def test_add_raises(self):
        qpath = QPath("store")
        try: qpath+None ; self.fail()
        except: pass
        try: qpath+"str" ; self.fail()
        except: pass

    def test_add_same(self):
        q1 = QPath("store")
        q2 = QPath("store")
        self.assertEqual(q1+q1, q1)
        self.assertEqual(q1+q2, q1)
        self.assertEqual(q1+q2, q2)

    def test_add_disjoint(self):
        self.assertIn(str(QPath("store.books.*.price")+QPath("..title")),
                      ("store.books.*.price|..title",
                       "..title|store.books.*.price"))

    def test_add_contains(self):
        q1 = QPath("store|..price")
        q2 = QPath("store")
        self.assertEqual(q1+q2, q1)
        self.assertEqual(q2+q1, q1)

    def test_add_merge(self):
        q1 = QPath("store|..price")
        q2 = QPath("store|..color")
        self.assertEqual(q1+q2, QPath("store|..price|..color"))

# -------------------------------------------------------------------

class Test_querypath(unittest.TestCase):

    def assertItemsEqual(self, iter1, iter2):
        """Assert that all the items in *iter1* are also in *iter2*
        regardless of the order."""
        lst = list(iter2)   # make a mutable copy
        try:
            for elem in iter1:
                lst.remove(elem)
        except ValueError:
            self.fail()
        self.assertFalse(lst)

    def setUp(self):
        self.maxDiff = None

# -------------------------------------------------------------------

    def test_None_get(self):
        path = None
        self.assertRaises(TypeError, querypath.get, self.obj, path)

    def test_None_test(self):
        path = None
        self.assertRaises(TypeError, querypath.get, self.obj, path)

# -------------------------------------------------------------------

    def test_empty_get(self):
        path = ""
        result = list(querypath.get(self.obj, path))
        expected = [self.obj]
        self.assertItemsEqual(result, expected)

    def test_empty_paths(self):
        path = ""
        result = list(querypath.paths(self.obj, path))
        expected = ['$']
        self.assertItemsEqual(result, expected)

    def test_empty_items(self):
        path = ""
        result = list(querypath.items(self.obj, path))
        expected = [('$', self.obj)]
        self.assertItemsEqual(result, expected)

    def test_empty_test(self):
        path = ""
        self.assertTrue(querypath.test(self.obj, path))

# -------------------------------------------------------------------

    def test_root_get(self):
        path = "$"
        result = list(querypath.get(self.obj, path))
        expected = [self.obj]
        self.assertItemsEqual(result, expected)

    def test_root_paths(self):
        path = "$"
        result = list(querypath.paths(self.obj, path))
        expected = ['$']
        self.assertItemsEqual(result, expected)

    def test_root_items(self):
        path = "$"
        result = list(querypath.items(self.obj, path))
        expected = [('$', self.obj)]
        self.assertItemsEqual(result, expected)

    def test_root_test(self):
        path = "$"
        self.assertTrue(querypath.test(self.obj, path))

# -------------------------------------------------------------------

    def test_empty_result_get(self):
        for path in (
            "folder",
            "$.folder",
            "$[folder]",
            "['folder']",
            "store.books.7",
            ):
            result = list(querypath.get(self.obj, path))
            expected = []
            self.assertItemsEqual(result, expected)


    def test_empty_result_paths(self):
        for path in (
            "folder",
            "$.folder",
            "$[folder]",
            "$[folder]",
            "['folder']",
            "store.books.7",
            ):
            result = list(querypath.get(self.obj, path))
            expected = []
            self.assertItemsEqual(result, expected)

    def test_empty_result_items(self):
        for path in (
            "folder",
            "$.folder",
            "$[folder]",
            "$[folder]",
            "['folder']",
            "store.books.7",
            ):
            result = list(querypath.get(self.obj, path))
            expected = []
            self.assertItemsEqual(result, expected)

    def test_empty_result_test(self):
        for path in (
            "folder",
            "$.folder",
            "$[folder]",
            "$[folder]",
            "['folder']",
            "store.books.7",
            ):
            self.assertFalse(querypath.test(self.obj, path))

# -------------------------------------------------------------------

    def test_single_get(self):
        for path in (
            "store.bicycle.color",
            "$.store.bicycle.color",
            "$['store']['bicycle']['color']",
            ):
            result = list(querypath.get(self.obj, path))
            expected = ["red"]
            self.assertItemsEqual(result, expected)

    def test_single_paths(self):
        for path in (
            "store.bicycle.color",
            "$.store.bicycle.color",
            "$['store']['bicycle']['color']",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = ['store.bicycle.color']
            self.assertItemsEqual(result, expected)

    def test_single_items(self):
        for path in (
            "store.bicycle.color",
            "$.store.bicycle.color",
            "$['store']['bicycle']['color']",
            ):
            result = list(querypath.items(self.obj, path))
            expected = [("store.bicycle.color", "red")]
            self.assertItemsEqual(result, expected)

    def test_single_test(self):
        for path in (
            "store.bicycle",
            "$.store.bicycle",
            "$['store']['bicycle']",
            ):
            self.assertTrue(querypath.test(self.obj, path))

# -------------------------------------------------------------------

    def test_numeric_get(self):
        for path in (
            "store.books.0.author",
            "store.books[0].author",
            ):
            result = list(querypath.get(self.obj, path))
            expected = ['Nigel Rees']
            self.assertItemsEqual(result, expected)

    def test_numeric_paths(self):
        for path in (
            "store.books.0.author",
            "store.books[0].author",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = ['store.books.0.author']
            self.assertItemsEqual(result, expected)

    def test_numeric_test(self):
        for path in (
            "store.books.0.author",
            "store.books[0].author",
            ):
            self.assertTrue(querypath.test(self.obj, path))

# -------------------------------------------------------------------

    def test_wildcard_get(self):
        for path in (
            "store.books.*.price",
            "['store']['books'][*]['price']",
            "['store']['books']['*']['price']",
            ):
            result = list(querypath.get(self.obj, path))
            expected = [8.95, 12.99, 8.99, 22.99]
            self.assertItemsEqual(result, expected)

    def test_wildcard_paths(self):
        for path in (
            "store.books.*.price",
            "['store']['books'][*]['price']",
            "['store']['books']['*']['price']",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = [
                'store.books.0.price',
                'store.books.1.price',
                'store.books.2.price',
                'store.books.3.price',
                ]
            self.assertItemsEqual(result, expected)

    def test_wildcard_test(self):
        for path in (
            "store.books.*.price",
            "['store']['books'][*]['price']",
            "['store']['books']['*']['price']",
            ):
            self.assertTrue(querypath.get(self.obj, path))

# -------------------------------------------------------------------

    def test_fullslice_get(self):
        for path in (
            "store.books[:].price",
            "store.books.:.price",
            "['store']['books'][':']['price']",
            "['store']['books'][:]['price']",
            ):
            result = list(querypath.get(self.obj, path))
            expected = [8.95, 12.99, 8.99, 22.99]
            self.assertItemsEqual(result, expected)

    def test_fullslice_paths(self):
        for path in (
            "store.books[:].price",
            "store.books.:.price",
            "['store']['books'][':']['price']",
            "['store']['books'][:]['price']",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = [
                'store.books.0.price',
                'store.books.1.price',
                'store.books.2.price',
                'store.books.3.price'
                ]
            self.assertItemsEqual(result, expected)

    def test_fullslice_test(self):
        for path in (
            "store.books[:].price",
            "store.books.:.price",
            "['store']['books'][':']['price']",
            "['store']['books'][:]['price']",
            ):
            self.assertTrue(querypath.test(self.obj, path))

# -------------------------------------------------------------------

    def test_slice_begin_get(self):
        for path in (
            "store.books[2:].price",
            "store.books.2:.price",
            "['store']['books']['2:']['price']",
            "['store']['books'][2:]['price']",
            ):
            result = list(querypath.get(self.obj, path))
            expected = [8.99, 22.99]
            self.assertItemsEqual(result, expected)

    def test_slice_begin_paths(self):
        for path in (
            "store.books[2:].price",
            "store.books.2:.price",
            "['store']['books']['2:']['price']",
            "['store']['books'][2:]['price']",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = [
                'store.books.2.price',
                'store.books.3.price',
                ]
            self.assertItemsEqual(result, expected)

    def test_slice_begin_test(self):
        for path in (
            "store.books[2:].price",
            "store.books.2:.price",
            "['store']['books']['2:']['price']",
            "['store']['books'][2:]['price']",
            ):
            self.assertTrue(querypath.get(self.obj, path))

# -------------------------------------------------------------------

    def test_slice_end_get(self):
        for path in (
            "store.books[:-1].price",
            "store.books.:-1.price",
            "['store']['books'][':-1']['price']",
            "['store']['books'][:-1]['price']",
            ):
            result = list(querypath.get(self.obj, path))
            expected = [8.95, 12.99, 8.99]
            self.assertItemsEqual(result, expected)

    def test_slice_end_paths(self):
        for path in (
            "store.books[:-1].price",
            "store.books.:-1.price",
            "['store']['books'][':-1']['price']",
            "['store']['books'][:-1]['price']",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = [
                'store.books.0.price',
                'store.books.1.price',
                'store.books.2.price',
                ]
            self.assertItemsEqual(result, expected)

    def test_slice_end_test(self):
        for path in (
            "store.books[:-1].price",
            "store.books.:-1.price",
            "['store']['books'][':-1']['price']",
            "['store']['books'][:-1]['price']",
            ):
            self.assertTrue(querypath.test(self.obj, path))

# -------------------------------------------------------------------

    def test_slice_step_get(self):
        for path in (
            "store.books[::2].price",
            "store.books.::2.price",
            "['store']['books']['::2']['price']",
            "['store']['books'][::2]['price']",
            ):
            result = list(querypath.get(self.obj, path))
            expected = [8.95, 8.99]
            self.assertItemsEqual(result, expected)

    def test_slice_step_paths(self):
        for path in (
            "store.books[::2].price",
            "store.books.::2.price",
            "['store']['books']['::2']['price']",
            "['store']['books'][::2]['price']",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = [
                'store.books.0.price',
                'store.books.2.price',
                ]
            self.assertItemsEqual(result, expected)

    def test_slice_step_test(self):
        for path in (
            "store.books[::2].price",
            "store.books.:2.price",
            "['store']['books']['::2']['price']",
            "['store']['books'][::2]['price']",
            ):
            self.assertTrue(querypath.test(self.obj, path))

# -------------------------------------------------------------------

    def test_recursive_descent_get(self):
        for path in (
            "store..price",
            "['store']..['price']",
            "$..price",
            "..price",
            ):
            result = list(querypath.get(self.obj, path))
            expected = [8.95, 12.99, 8.99, 22.99, 19.95]
            self.assertItemsEqual(result, expected)

    def test_recursive_descent_paths(self):
        for path in (
            "store..price",
            "['store']..['price']",
            "$..price",
            "..price",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = [
                'store.books.0.price',
                'store.books.1.price',
                'store.books.2.price',
                'store.books.3.price',
                'store.bicycle.price',
                ]
            self.assertItemsEqual(result, expected)

    def test_recursive_descent_test(self):
        for path in (
            "store..price",
            "$['store']..['price']",
            "$..price",
            "$..price",
            ):
            self.assertTrue(querypath.get(self.obj, path))

# -------------------------------------------------------------------

    def test_comma_union_get(self):
        for path in (
            "store.books,bicycle,car..price",
            "$['store']['books,bicycle']..['price']",
            ):
            result = list(querypath.get(self.obj, path))
            expected = [8.95, 12.99, 8.99, 22.99, 19.95]
            self.assertItemsEqual(result, expected)

    def test_comma_union_paths(self):
        for path in (
            "store.books,bicycle,car..price",
            "$['store']['books,bicycle']..['price']",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = [
                'store.books.0.price',
                'store.books.1.price',
                'store.books.2.price',
                'store.books.3.price',
                'store.bicycle.price',
                ]
            self.assertItemsEqual(result, expected)

    def test_comma_union_test(self):
        for path in (
            "store.books,bicycle,car..price",
            "$['store']['books,bicycle']..['price']",
            ):
            self.assertTrue(querypath.get(self.obj, path))

# -------------------------------------------------------------------

    def test_pipe_union_get(self):
        for path in (
            "..books.*.category|..bicycle.color",
            "..books.*.category |..bicycle.color",
            "..books.*.category| ..bicycle.color",
            "..books.*.category | ..bicycle.color",
            "[store][books][:][category]|[store][bicycle][color]",
            "store.books.*.category|store.bicycle.color",
            ):
            result = list(querypath.get(self.obj, path))
            expected = [
                'reference',
                'fiction',
                'fiction',
                'fiction',
                'red',
                ]
            self.assertItemsEqual(result, expected)

    def test_pipe_union_paths(self):
        for path in (
            "..books.*.category|..bicycle.color",
            "..books.*.category |..bicycle.color",
            "..books.*.category| ..bicycle.color",
            "..books.*.category | ..bicycle.color",
            "[store][books][:][category]|[store][bicycle][color]",
            "store.books.*.category|store.bicycle.color",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = [
                'store.books.0.category',
                'store.books.1.category',
                'store.books.2.category',
                'store.books.3.category',
                'store.bicycle.color',
                ]
            self.assertItemsEqual(result, expected)

    def test_pipe_union_test(self):
        for path in (
            "..books.*.category|..bicycle.color",
            "..books.*.category |..bicycle.color",
            "..books.*.category| ..bicycle.color",
            "..books.*.category | ..bicycle.color",
            "[store][books][:][category]|[store][bicycle][color]",
            "store.books.*.category|store.bicycle.color",
            ):
            self.assertTrue(querypath.test(self.obj, path))

    def test_pipe_union_empty(self):
        for path in (
            "|..bicycle.color",
            "..bicycle.color|",
            ):
            result = list(querypath.get(self.obj, path))
            expected = [self.obj, 'red']
            self.assertItemsEqual(result, expected)

    def test_pipe_intersection_get(self):
        result = querypath.get(self.obj, "..price|store.books[0].price")
        expected = [8.95, 12.99, 8.99, 22.99, 19.95]
        self.assertItemsEqual(result, expected)

    def test_pipe_intersection_paths(self):
        result = querypath.paths(self.obj, "..price|store.books[0].price")
        expected = [
            'store.books.0.price',
            'store.books.1.price',
            'store.books.2.price',
            'store.books.3.price',
            'store.bicycle.price',
            ]
        self.assertItemsEqual(result, expected)

# -------------------------------------------------------------------

    def test_script_index_get(self):
        for path in (
            "..books[(@.__len__()-1)].isbn",
            "..['books'][(@.__len__()-1)]['isbn']",
            ):
            result = list(querypath.get(self.obj, path))
            expected = ["0-395-19395-8"]
            self.assertItemsEqual(result, expected)

    def test_script_index_paths(self):
        for path in (
            "..books[(@.__len__()-1)].isbn",
            "..['books'][(@.__len__()-1)]['isbn']",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = ['store.books.3.isbn']
            self.assertItemsEqual(result, expected)

    def test_script_index_test(self):
        for path in (
            "..books[(@.__len__()-1)].isbn",
            "..['books'][(@.__len__()-1)]['isbn']",
            ):
            self.assertTrue(querypath.get(self.obj, path))

# -------------------------------------------------------------------

class Test_querypath_containers(Test_querypath):

    def setUp(self):
        super().setUp()
        self.obj = {
            "store": {
                "books": [
                    {
                        "category": "reference",
                        "author": "Nigel Rees",
                        "title": "Sayings of the Century",
                        "price": 8.95
                        },
                    {
                        "category": "fiction",
                        "author": "Evelyn Waugh",
                        "title": "Sword of Honour",
                        "price": 12.99
                        },
                    {
                        "category": "fiction",
                        "author": "Herman Melville",
                        "title": "Moby Dick",
                        "isbn": "0-553-21311-3",
                        "price": 8.99
                        },
                    {
                        "category": "fiction",
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

    def test_all_items(self):
        obj = {
            "i": 1,
            "f": 0.1,
            "s": "str",
            "l": [1, 2, 3],
            "d": {
                "i": 1,
                "f": 0.1,
                "s": "str",
                },
            }
        result = querypath.get(obj, "..*")
        expected = [
            1, 0.1, "str", "s", "t", "r", "s", "t", "r",
            [1, 2, 3], 1, 2, 3,
            {
                "i": 1,
                "f": 0.1,
                 "s": "str",
                },
            1, 0.1, "str", "s", "t", "r", "s", "t", "r",
            ]
        self.assertItemsEqual(result, expected)

    def test_wildcard(self):
        wildcard = object()
        obj = {
            "i": 1,
            "f": 0.1,
            "d": {
                "inner": wildcard,
                "container": {
                    "value": 1,
                    },
                },
            }
        self.assertTrue(querypath.test(obj, "d.inner.unexistant", wildcard))
        self.assertFalse(querypath.test(obj, "d.container.unexistant", wildcard))

    def test_script_query_get(self):
        result = querypath.get(self.obj, "..books.*[?(@['price']<10)].title")
        expected = ['Sayings of the Century', 'Moby Dick']
        self.assertItemsEqual(result, expected)

    def test_script_query_paths(self):
        result = querypath.paths(self.obj, "..books.*[?(@['price']<10)].title")
        expected = ['store.books.0.title', 'store.books.2.title']
        self.assertItemsEqual(result, expected)

    def test_script_query_test(self):
        self.assertTrue(
            querypath.test(self.obj, "..books.*[?(@['price']<10)].title"))

    def test_script_query2_get(self):
        for path in (
            "..books.*[?('isbn' in @)].title",
            "..books.*[?(@['isbn'])].title",
            ):
            result = list(querypath.get(self.obj, path))
            expected = [
                'Moby Dick',
                'The Lord of the Rings',
                ]
            self.assertItemsEqual(result, expected)

    def test_script_query2_paths(self):
        for path in (
            "..books.*[?('isbn' in @)].title",
            "..books.*[?(@['isbn'])].title",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = [
                'store.books.2.title',
                'store.books.3.title',
                ]
            self.assertItemsEqual(result, expected)

    def test_script_query2_test(self):
        for path in (
            "..books.*[?('isbn' in @)].title",
            "..books.*[?(@['isbn'])].title",
            ):
            self.assertTrue(querypath.get(self.obj, path))

# -------------------------------------------------------------------

class Test_querypath_objects(Test_querypath):

    def setUp(self):
        super().setUp()
        class Book:
            def __init__(self, category, author, title, price):
                self.category = category
                self.author = author
                self.title = title
                self.price = price
        class Bicycle:
            def __init__(self, color, price):
                self.color = color
                self.price = price
        class Container:
            def __init__(self, store):
                self.store = store
        books = [
            Book("reference", "Nigel Rees", "Sayings of the Century", 8.95),
            Book("fiction", "Evelyn Waugh", "Sword of Honour", 12.99),
            Book("fiction", "Herman Melville", "Moby Dick", 8.99),
            Book("fiction", "J. R. R. Tolkien", "The Lord of the Rings", 22.99),
            ]
        books[2].isbn = "0-553-21311-3"
        books[3].isbn = "0-395-19395-8"
        self.obj = Container({"books": books, "bicycle": Bicycle("red", 19.95)})

    def test_all_items(self):
        class A:
            def __init__(self, a=None):
                self.i = 1
                self.f = 0.1
                self.s = "str"
                self.l = [1,2,3]
                self.a = a
            def __eq__(self, o):
                return isinstance(o,A) \
                    and self.i==o.i and self.f==o.f and self.s==o.s and self.l==o.l
        obj = A(A())
        result = querypath.get(obj, "..*")
        expected = [
            1, 0.1, "str", "s", "t", "r", "s", "t", "r",
            [1, 2, 3], 1, 2, 3,
            A(),
            1, 0.1, "str", "s", "t", "r", "s", "t", "r",
            [1, 2, 3], 1, 2, 3,
            None,
            ]
        self.assertItemsEqual(result, expected)

    def test_wildcard(self):
        wildcard = object()
        class A:
            def __init__(self, a=None):
                self.i = 1
                self.s = wildcard
                self.a = a
        obj = A(A())
        self.assertTrue(querypath.test(obj, "a.s.unexistant", wildcard))
        self.assertFalse(querypath.test(obj, "a.a.unexistant", wildcard))

    def test_script_query_get(self):
        result = querypath.get(self.obj, "..books.*[?(@.price<10)].title")
        expected = ['Sayings of the Century', 'Moby Dick']
        self.assertItemsEqual(result, expected)

    def test_script_query_paths(self):
        result = querypath.paths(self.obj, "..books.*[?(@.price<10)].title")
        expected = ['store.books.0.title', 'store.books.2.title']
        self.assertItemsEqual(result, expected)

    def test_script_query_test(self):
        self.assertTrue(
            querypath.test(self.obj, "..books.*[?(@.price<10)].title"))

    def test_script_query2_get(self):
        for path in (
            "..books.*[?(@.isbn)].title",
            "..books.*[?('isbn' in @.__dict__)].title",
            ):
            result = list(querypath.get(self.obj, path))
            expected = [
                'Moby Dick',
                'The Lord of the Rings',
                ]
            self.assertItemsEqual(result, expected)

    def test_script_query2_paths(self):
        for path in (
            "..books.*[?(@.isbn)].title",
            "..books.*[?('isbn' in @.__dict__)].title",
            ):
            result = list(querypath.paths(self.obj, path))
            expected = [
                'store.books.2.title',
                'store.books.3.title',
                ]
            self.assertItemsEqual(result, expected)

    def test_script_query2_test(self):
        for path in (
            "..books.*[?(@.isbn)].title",
            "..books.*[?('isbn' in @.__dict__)].title",
            ):
            self.assertTrue(querypath.get(self.obj, path))

# -------------------------------------------------------------------

def suite():
    testcases = (
        Test_querypath_containers,
        Test_querypath_objects,
        Test_QPath,
        )
    return unittest.TestSuite(itertools.chain(
            *(map(t, filter(lambda f: f.startswith("test_"), dir(t))) \
                  for t in testcases)))

# -------------------------------------------------------------------

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite())
