=====================================================
 :mod:`boing.utils.url` --- Uniform Resource Locator
=====================================================

.. module:: boing.utils.url
   :synopsis: Uniform Resource Locator

The module :mod:`boing.utils.url` mainly provides the class
:class:`URL`, which is used to represent a Uniform Resource Locator.

.. class:: URL(string)

   An instance of the class :class:`URL` represents an Uniform
   Resource Locator (URL). The attribute *string* of the class
   constuctor defines the URL that the instance will represent; at the
   instance initialization, *string* is parsed in order to detect the kind
   of URL and to separate it into the specific components: *schema*,
   *site*, *path*, *query*, *fragment*.

   Usage example::

      >>> from boing.utils.url import URL
      >>> url = URL("ftp://paolo:pwd@localhost:8888/temp?key=value#frag")
      >>> url.scheme
      'ftp'
      >>> url.site.user
      'paolo'
      >>> url.site.password
      'pwd'
      >>> url.site.host
      'localhost'
      >>> url.site.port
      8888
      >>> str(url.path)
      '/temp'
      >>> url.query['key']
      'value'
      >>> url.fragment
      'frag'

   Each instance owns the following read-only attributes:

   .. attribute:: kind

      Kind of URL. It equals
      to one of the following:

      - :const:`URL.EMPTY` --- empty URL
      - :const:`URL.OPAQUE` --- URL like ``<scheme>:<opaque>``
      - :const:`URL.GENERIC` --- URL like ``<scheme>://<site>/<path>?<query>#<fragment>``
      - :const:`URL.NETPATH` --- URL like ``//<site>/<path>?<query>#<fragment>``
      - :const:`URL.ABSPATH` --- URL like ``/<path>?<query>#<fragment>``
      - :const:`URL.RELPATH` --- URL like ``<path>?<query>#<fragment>``

   .. attribute:: scheme

      URL scheme defined by a :class:`str`.

   .. attribute:: site

      URL site defined by an instance of the class :class:`URL_site`.

   .. attribute:: path

      URL path defined by an instance of the class :class:`URL_path`.

   .. attribute:: query

      URL query defined by an instance of the class :class:`URL_query`.

   .. attribute:: fragment

      URL fragment defined by a :class:`str`.

   .. attribute:: opaque

      if the URL is of kind :const:`URL.OPAQUE` it defines the right part of the URL;
      otherwise it is set by default to the empty string ``""``.

   The string representation of an :class:`URL` instance is normally
   equal to the string passed at the instance initialization, but
   there are few exceptions::

      >>> str(URL("udp://:3333"))
      'udp://:3333'
      >>> str(URL("udp://:3333:0"))
      'udp://:3333'
      >>> str(URL("file:/tmp/log"))
      'file:///tmp/log'

   :class:`URL` instances are equal if their string representation is the same::

      >>> URL("udp://:3333")==URL("udp://:3333")
      True
      >>> URL("udp://:3333:0")==URL("udp://:3333")
      True


   :class:`URL` instances can be compared to :class:`str` objects::

      >>> URL("udp://:3333")=="udp://:3333"
      True

   and they can be concatenated as they were :class:`str` objects::

      >>> url = URL("udp://:3333")
      >>> "osc."+url
      'osc.udp://:3333'
      >>> url+"#frag"
      'udp://:3333#frag'

   Note that the result is a :class:`str`, not an :class:`URL` instance.

URL internal classes
====================

.. class:: URL_site(string)

   Used to store the component *site* of an URL. Each instance owns
   the following attributes:

   .. attribute:: user

      User defined by a string.

   .. attribute:: password

      Password defined by a string. It is NOT encripted.

   .. attribute:: host

      Site host defined by a string.

   .. attribute:: port

      Port number defined by an integer. It defaults to ``0``.

   Usage example::

      >>> url = URL("ftp://paolo:pwd@localhost:8888")
      >>> url.site
      URL_site('paolo:pwd@localhost:8888')
      >>> print(url.site)
      paolo:pwd@localhost:8888
      >>> url.site.user
      'paolo'
      >>> url.site.password
      'pwd'
      >>> url.site.host
      'localhost'
      >>> url.site.port
      8888

   Instances can be compared to :class:`str` objects::

      >>> url = URL("udp://localhost:3333")
      >>> url.site=="localhost:3333"
      True

   and have Boolean value to ``True`` if anyone of the component
   attributes is defined::

      >>> bool(URL("udp://localhost:3333").site)
      True
      >>> bool(URL("udp://").site)
      False


   .. warning::

         Pay attention to the default case::

            >>> bool(URL("udp://:0").site)
            False

.. class:: URL_path(string)

   Used to store the component *path* of an URL. Usage example::

      >>> url = URL("file:///tmp/log")
      >>> url.path
      URL_path('/tmp/log')
      >>> print(url.path)
      /tmp/log
      >>> url.path.isAbsolute()
      True

   .. method:: isAbsolute

      Return wheter the path is absolute::

	 >>> URL("file:///tmp/log").path.isAbsolute()
	 True
	 >>> URL("/tmp/log").path.isAbsolute()
	 True
	 >>> URL("file").path.isAbsolute()
	 False
	 >>> URL("./file").path.isAbsolute()
	 False


   Instances can be compared to :class:`str` objects::

      >>> url = URL("file:///tmp/log")
      >>> url.path=="/tmp/log"
      True

   and have Boolean value to ``True`` if the URL path is not empty::

      >>> bool(URL("file:///tmp/log").path)
      True
      >>> bool(URL("/").path)
      True
      >>> bool(URL("udp://:8888").path)
      False

   .. warning::

         Pay attention to the default transformation::

            >>> str(URL("file:/tmp/log"))
	    'file:///tmp/log'

.. class:: URL_query(string)

   Used to store the component *query* of an URL. This class implements the
   :class:`collections.MutableMapping` *ABC*. It is also able to encode the
   URL's *query* into a “percent-encoded” string.

   Usage examples::

      >>> url = URL("udp://:8888?name=Jérémie&connect")
      >>> url
      URL('udp://:8888?name=J%e9r%e9mie&connect')
      >>> url.query
      URL_query('name=J%e9r%e9mie&connect')
      >>> url.query['name']
      'Jérémie'
      >>> dict(url.query)
      {'name': 'Jérémie', 'connect': ''}
      >>> URL("udp://:8888?name=Jérémie&connect")==URL("udp://:8888?name=J%e9r%e9mie&connect")
      True
