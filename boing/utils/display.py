#########################
# COMMENTED SINCE UNUSED
#########################
# # -*- coding: utf-8 -*-
# #
# # boing/utils/display.py -
# #
# # Author: Paolo Olivo (paolo.olivo@inria.fr)
# #
# # Copyright © INRIA
# #
# # See the file LICENSE for information on usage and redistribution of
# # this file, and for a DISCLAIMER OF ALL WARRANTIES.

# from boing.utils.url import URL

# mmPerInch = 25.4

# class DisplayDevice(object):
#     """Abstract class for defining a generic display device."""

#     @staticmethod
#     def create(url=None):
#         global factorymethod
#         return factorymethod(url)

#     @property
#     def bounds(self):
#         """Return display bounds in pixels."""
#         raise NotImplementedError

#     @property
#     def size(self):
#         """Return display size in millimiters."""
#         raise NotImplementedError

#     @property
#     def resolution(self):
#         """Return display resolution in dpi."""
#         bounds = self.bounds
#         size = self.size
#         if size.width and size.height:
#             global mmPerInch
#             hDPI = self.bounds.size.width * mmPerInch / self.size.width
#             vDPI = self.bounds.size.height * mmPerInch / self.size.height
#             return (hDPI, vDPI)
#         return (0,0)

#     @property
#     def refreshrate(self):
#         """Return display refresh rate in Hz."""
#         raise NotImplementedError

#     @property
#     def url(self):
#         """Return the display url."""
#         raise NotImplementedError

#     def mm2pixels(self, pos, trunc=False):
#         """Determine the pixel correspondent to the position pos
#         defined in millimiters."""
#         dpi = self.resolution
#         x = pos[0]/mmPerInch*dpi[0]
#         y = pos[1]/mmPerInch*dpi[1]
#         if trunc: return int(x), int(y)
#         else: return x,y

#     def debug(self):
#         bounds = self.bounds
#         size = self.size
#         res = self.resolution
#         print("url: \"%s\""%self.url)
#         print("bounds (in pixels):", self.bounds)
#         print("size (in mm):", self.size)
#         print("resolution: %dx%d ppi"%(round(res[0]), round(res[1])))
#         print("refresh rate: %g Hz"%self.refreshrate)

# # --------------------------------------------------------------------------
# try:
#     # Use libpointing bindings
#     from pylibpointing import Size, Point, Bounds
#     from pylibpointing import DisplayDevice as __DisplayDevice
#     from pylibpointing import DummyDisplayDevice as __DummyDisplayDevice

#     class LibPointingDisplayDevice(__DisplayDevice, DisplayDevice):
#         @property
#         def url(self):
#             """Return the display url."""
#             return URL(str(self.getURI()))

#     class LibPointingDummyDisplayDevice(__DummyDisplayDevice, DisplayDevice):
#         @property
#         def url(self):
#             """Return the display url."""
#             return URL(str(self.getURI()))

#     def factorymethod(uri=None):
#         if uri is None: uri = "any:"
#         if str(uri).startswith("dummy:"):
#             return LibPointingDummyDisplayDevice(uri)
#         else:
#             return LibPointingDisplayDevice(uri)

#     USING_PYLIBPOINTING = True
# except:
#     print("WARNING! Module pylibpointing not available.")
#     USING_PYLIBPOINTING = False

# if not USING_PYLIBPOINTING:
#     # Use own classes
#     class Size(object):
#         def __init__(self, width, height):
#             self.width = width
#             self.height = height

#         def __str__(self):
#             return "%gx%g"%(self.width, self.height)

#         def __eq__(self, other):
#             return isinstance(other, Size) and self.width==other.width and self.height==other.height

#         def __ne__(self, other):
#             return not self==other

#     class Point(object):
#         def __init__(self, x, y):
#             self.x = x
#             self.y = y

#         def __str__(self):
#             return "(%g,%g)"%(self.x, self.y)

#         def __eq__(self, other):
#             return isinstance(other, Point) and self.x==other.x and self.y==other.y

#         def __ne__(self, other):
#             return not self==other

#     class Bounds(object):
#         def __init__(self, x, y, width, height):
#             self.origin = Point(x, y)
#             self.size = Size(width, height)

#         def __str__(self):
#             return "origin=%s size=%s"%(self.origin, self.size)

#         def __eq__(self, other):
#             return isinstance(other, Bounds) and self.origin==other.origin and self.size==other.size

#         def __ne__(self, other):
#             return not self==other

#     class DummyDisplayDevice(DisplayDevice):
#         def __init__(self, url=None):
#             super(DummyDisplayDevice, self).__init__()
#             url = url if isinstance(url, URL) else URL(url)
#             w = float(url.query.get('w', 0))
#             h = float(url.query.get('h', 0))
#             self._size = Size(w, h)
#             bx = float(url.query.get('bx', 0))
#             by = float(url.query.get('by', 0))
#             bw = float(url.query.get('bw', 0))
#             bh = float(url.query.get('bh', 0))
#             self._bounds = Bounds(bx, by, bw, bh)
#             ppi = float(url.query.get('ppi', 75))
#             self._resolution = (ppi, ppi)
#             hz = float(url.query.get('hz', 0))
#             self._refreshrate = hz

#         @property
#         def bounds(self):
#             return self._bounds

#         @property
#         def size(self):
#             return self._size

#         @property
#         def resolution(self):
#             if self._resolution==(0,0):
#                 return DisplayDevice.resolution(self)
#             else:
#                 return self._resolution

#         @property
#         def refreshrate(self):
#             return self._refreshrate

#         @property
#         def url(self):
#             url = "dummy:?"
#             url += "w=%i"%self._size.width
#             url += "&h=%i"%self._size.height
#             url += "&bx=%i"%self._bounds.origin.x
#             url += "&by=%i"%self._bounds.origin.y
#             url += "&bw=%i"%self._bounds.size.width
#             url += "&bh=%i"%self._bounds.size.height
#             url += "&ppi=%i"%int((self._resolution[0]+self._resolution[1])*0.5)
#             url += "&hz=%i"%self._refreshrate
#             return URL(url)

#         def setBounds(self, bounds):
#             self._bounds = Bounds(bounds.origin.x, bounds.origin.y, bounds.size.width, bounds.size.height)

#         def setSize(self, size):
#             self._size = Size(size.width, size.height)

#         def setResolution(self, vref, href=None):
#             if href is None: href = vref
#             self._resolution = (vref, href)

#         def setRefreshRate(self, refreshrate):
#             self._refreshrate = refreshrate

#     def factorymethod(url=None):
#         if url is None or url=="": url = "any:"
#         url = url if isinstance(url, URL) else URL(url)
#         anywilldo = True if url.scheme=="any" else False
#         if anywilldo or url.scheme=="dummy":
#             return DummyDisplayDevice(url)
#         raise ValueError('Unsupported display device: "%s"'%url)

# # --------------------------------------------------------------------------

# if __name__=="__main__":
#     import getopt
#     import sys
#     try:
#         opts, args = getopt.getopt(sys.argv[1:], "h", ['help'])
#     except getopt.GetoptError as err:
#         print(str(err)) # will print something like "option -a not recognized"
#         print("usage: %s [<url>]"%sys.argv[0])
#         print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
#         sys.exit(2)

#     for o, a in opts:
#         if o in ("-h", "--help"):
#             print("usage: %s [<url>]"%sys.argv[0])
#             print("       %s [-h, --help]"%(" "*len(sys.argv[0])))
#             print("""
#     Open a display device and print its statistics.

#     Options:
#      -h, --help                 display this help and exit

#     Available URLs:
#      dummy:[?ppi=96&hz=60&bx=0&by=0&bw=0&bh=0&w=0&h=0]
#        Dummy device with specified resolution, bounds and size.

#      any:
#        Any of the platform-specific devices below.

#      xorgdisplay:[<display name>]
#        The specified X11 display of the form [hostname]:displaynumber[.screennumber].
#        (LINUX ONLY)

#      windisplay:
#        Specific display device for MS Windows OS.
#        (WINDOWS ONLY)
#     """)
#             sys.exit(0)

#     url = args[0] if len(args)>0 else None
#     display = DisplayDevice.create(url)
#     display.debug()
