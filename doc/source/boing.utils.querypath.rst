========================================================
 :mod:`boing.utils.querypath` --- A query path language
========================================================

.. module:: boing.utils.querypath
   :synopsis: A query path language

The module :mod:`boing.utils.querypath` provides *Querypath*, a query
language that can be used to handle hierarchical data structures, no
matter if they are composed of standard containers, e.g. :class:`list`
or :class:`dict`, or instances of standard or custom classes.

The proposed *querypath* language is a derivation of JSONPath_, which
was proposed by Stefan Goessner to handle JSON_ structures. Beyond
some minor changes, the |boing|'s query language exploits the fact
that the attributes of Python class instances are stored inside the
attribute ``__dict__``, by actually treating the instances of not
Container classes as they were dictionaries.

The root object is indexed using the character ``$``, but it can be
omitted.

*Querypath* expressions can use the dot–notation::

   contacts.0.x

or the bracket–notation::

   ['contacts'][0]['x']

or a mix of them::

   contacts[0][x]

*Querypath* allows the wildcard symbol ``*`` for member names and
array indices, the descendant operator ``..`` and the array slice
syntax ``[start:end:step]``.

Python expressions can be used as an alternative to explicit names or
indices using the syntax ``[(<expr>)]``, as for example::

   contacts[(@.__len__()-1)].x

using the symbol ``@`` for the current object. Also consider that
built-in functions and classes are not available. Filter expressions
are supported via the syntax ``[?(<boolean expr>)]`` as in::

   contacts.*[?(@.x<10)]

In order to access to multiple items that have the same parent, it is
possible to use the operator ``,``, as in::

   props.width,height

while for selecting multiple items that have different parents, it is
necessary to combine two *Querypaths* using the operator ``|``, as
in::

   props.*|contact..x

Note that the ``,`` structure is normally quicker than the ``|``
structure, since in the latter case the query always restarts from the
root object. Indexing all the values of the data model is possible
using the path ``..*``.

The module :mod:`boing.utils.querypath` provides a set of static
functions for executing *Querypath* expression on user data
structures. The query expression must be provided as standard strings.

.. function:: get(obj, path)

   Return an iterator over the *obj*'s attributes or items matched by
   *path*.

.. function:: paths(obj, path)

   Return an iterator over the paths that index the *obj*'s attributes
   or items matched by *path*.

.. function:: items(obj, path)

   Return an iterator over the pairs (path, value) of the *obj*'s
   items that are matched by *path*.

.. function:: test(obj, path, wildcard=NOWILDCARD)

   Return whether at least one *obj*'s attributes or items is matched
   by *path*. The object *wildcard* matches even if *path* does not
   completely match an item in obj.

.. attribute:: NOWILDCARD

   Option specifing that the method :func:`test` should not consider
   any wildcard.

Usage examples
==============

   >>>   class Contact:
   ...      def __init__(self, x, y):
   ...         self.x = x
   ...         self.y = y
   ...      def polar(self):
   ...         return math.sqrt(x*x, y*y), math.atan2(y,x)
   ...      def __repr__(self):
   ...         return "Contact(%s,%s)"%(self.x, self.y)
   ...
   >>>   class Surface:
   ...      def __init__(self):
   ...         self.contacts = []
   ...         self.props = {}
   ...
   >>> table = Surface()
   >>> table.props['width'] = 800
   >>> table.props['height'] = 600
   >>> table.props['id'] = "mytable"
   >>> table.contacts.append(Contact(100,200))
   >>> table.contacts.append(Contact(500,600))
   >>> tuple(querypath.get(table, "contacts.0.x"))
   (100,)
   >>> tuple(querypath.get(table, "contacts.*.x"))
   (100, 500)
   >>> tuple(querypath.get(table, "props.width,height"))
   (600, 800)
   >>> tuple(querypath.get(table, "..y"))
   (200, 600)
   >>> tuple(querypath.get(table, "contacts.*[?(@.x<=100)]"))
   (Contact(100,200),)
   >>> tuple(querypath.get(table, "contacts.*.x,y|props.*"))
   (600, 500, 800, 200, 100, 600, "mytable")
   >>> tuple(querypath.paths(table, "props.*"))
   ('props.height', 'props.width')
   >>> tuple(querypath.items(table, "contacts.*"))
   (('contacts.1', Contact(100,200)), ('contacts.2', Contact(500,600)))
   >>> querypath.test(table, "props.dpi")
   False
   >>> querypath.test(table, "contacts.*[?(@.x>100)]")
   True
   >>> querypath.test(table, "props.width.mm")
   False
   >>> querypath.test(table, "props.width.mm", wildcard=800)
   True

The :class:`QPath` class
========================

Since *Querypath* strings must be pre-processed in order to be
executed, supposing you are going to use the same query multiple
times, it may be better to create a :class:`QPath` instance, and then
use the member methods, instead of the :mod:`boing.utils.querypath`
static functions. The proposed functuality is equal, but the string
does not have to be pre-processed for all the executions.

.. class:: QPath(path)

   A compiled *Querypath* expression.

   .. method:: get(obj)

      Return an iterator over the *obj*'s attributes or items matched
      by this QPath.

   .. method:: paths(obj)

      Return an iterator over the paths that index the *obj*'s
      attributes or items matched by this QPath.

   .. method:: items(obj)

      Return an iterator over the pairs (path, value) of the *obj*'s
      items that are matched by this QPath.

   .. method:: test(obj, wildcard=NOWILDCARD)

      Return whether this QPath matches at least one *obj*'s
      attributes or items. The object *wildcard* matches even if
      *path* does not completely match an item in obj.

   *Usage example*::

      >>> query = querypath.QPath("contacts.*.x")
      >>> tuple(query.get(table))
      (100, 500)
      >>> tuple(query.paths(table))
      ('contacts.0.x', 'contacts.1.x')
      >>> tuple(query.items(table))
      (('contacts.0.x', 100), ('contacts.1.x', 500))
      >>> query.test(table)
      True

   :class:`QPath` instances can be combined using the ``+``
   operator. This operation concatenates the operand strings using the
   ``|`` delimiter, but it also tries to optimize the result by
   avoiding expression duplicates, as in::

      >>> querypath.QPath("props")+querypath.QPath("contacts")
      QPath('contacts|props')
      >>> querypath.QPath("props")+querypath.QPath("props")
      QPath('props')

   Still it cannot optimize more complex overlaps::

      >>> querypath.QPath("contacts[0]")+querypath.QPath("contacts.*")
      QPath('contacts[0]|contacts.*')



.. _JSON: http://www.json.org
.. _JSONPath: http://goessner.net/articles/JsonPath/
