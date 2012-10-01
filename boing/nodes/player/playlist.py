# -*- coding: utf-8 -*-
#
# boing/nodes/player/playlist.py -
#
# Copyright © INRIA
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import os
import weakref

from PyQt4 import QtGui, QtCore
import xml.etree.ElementTree as xmlET

from boing import config as _config
from boing.nodes.player import EXTENSION

# -------------------------------------------------------------------
# Tree structure
class TElem:
    """This class defines the basic element of the tree: an element
    that can be attached to a TNode.

    """
    def __init__(self):
        self._parent = None
        self.data = None

    def attachTo(self, parent):
        """Attach this element to *parent*."""
        parent.attach(self)

    def detachFromParent(self):
        """Detach this element from its parent."""
        if self._parent is not None: self._parent.detachChild(self)

    def parent(self): return self._parent

    def ancestors(self):
        """Get the list of ancestors."""
        if self._parent is None: rvalue = list()
        else:
            ancestors = [self._parent]
            ancestors.extend(self._parent.ancestors())
            rvalue = ancestors
        return rvalue

    def hasAncestor(self, ancestor):
        """Return whether *ancestor* is an ancestor of this element."""
        return self.parent() is not None \
            and (self.parent() is ancestor or self.parent().hasAncestor(ancestor))

    def __str__(self): return '[TElem %s]'%str(self.data)


class TNode(TElem):
    """This class defines the basic Node of the Tree. A TNode can hold
    TElem.

    """
    def __init__(self):
        super().__init__()
        self._children = []

    def attachChild(self, child, index=None):
        """ Attach a TElem to this TNode. Return the number of
        children of this TNode after that the new child has been
        attached."""
        if index is None: index = len(self._children)
        if child._parent is not None: child.detachFromParent()
        self._children[index:index] = [child]
        child._parent = self
        return len(self._children)

    def attachChildren(self, children, index=None):
        """It attaches a list of TElem to this TNode. Return the
        number of children of this TNode after that the new child has
        been attached."""
        if index is None: index = len(self._children)
        for elem in children:
            if elem._parent is not None: elem.detachFromParent()
            elem._parent = self
        self._children[index:index] = children
        return len(self._children)

    def detachChild(self, child):
        """ Detach *child*. Return *child* if it was a child a self,
        otherwise None."""
        if child.parent() is self:
            self._children.remove(child)
            child._parent = None
            rvalue = child
        else:
            rvalue = None
        return rvalue

    def detachChildAt(self, index):
        """Detach and return the child at the given *index*."""
        child = self._children.pop(index)
        child._parent = None
        return child

    def detachChildrenAt(self, iIndex, eIndex):
        """Detach and return the children between the given indexes."""
        children = self._children[iIndex:eIndex]
        del self._children[iIndex:eIndex]
        for child in children:
            child._parent = None
        return children

    def detachChildren(self):
        """Detach and return all the children."""
        for child in self._children:
            child._parent = None
        rvalue = self._children
        self._children = list()
        return rvalue

    def children(self): return self._children
    def childAt(self, index): return self._children[index]
    def index(self, child): return self._children.index(child)

    def __str__(self):
        rvalue = '[TNode %s'%str(self.data)
        for child in self._children:
            rvalue += ' %s'%str(child)
        rvalue += ']'
        return rvalue

# -------------------------------------------------------------------

class File:
    """This class maps a file."""
    def __init__(self, filepath):
        self._dirpath, self._filename = os.path.split(os.path.normpath(filepath))
        # Retrieve the size of this file
        file_stat = os.stat(self.filepath())
        # Size of the file in bytes
        self._size = file_stat.st_size

    def filepath(self): return '%s/%s'%(self._dirpath, self._filename)
    def filename(self): return self._filename

    def size(self):
        """Return the size of this track in bites."""
        return self._size

    def __str__(self): return '[File %s/%s]'%(self._dirpath, self._filename)


class Track(TElem, File):
    """This class represents a single track of the playlist."""
    def __init__(self, filepath, valid):
        TElem.__init__(self)
        File.__init__(self, filepath)
        self._valid = valid

    def valid(self): return self._valid

    def firstValid(self):
        """Return self if it is valid, otherwise None."""
        return self if self.valid() else None

    def __str__(self): return '[Track %s/%s]'%(self._dirpath, self._filename)


class ListFolder(TNode):
    """This class represents a virtual folder in the playlist. It does
    not map a real directory in the filesystem."""
    def __init__(self, name):
        """Create a new virtual folder with the provided name."""
        super().__init__()
        self._name = str(name)
        self._expanded = False

    def name(self):
        """This returns the folder's name."""
        return self._name

    def size(self):
        """Return the number of items contained by this folder."""
        return len(self._children)

    def expanded(self): return self._expanded

    def firstValid(self):
        for child in self.children():
            rvalue = child.firstValid()
            if rvalue is not None: break
        else:
            rvalue = None
        return rvalue

    def __str__(self): return '[ListFolder %s %s]'%(self._name, self._expanded)


class Playlist(QtCore.QAbstractItemModel):
    """This class defines the model of the Playlist. Inheriting the
    QAbstractItemModel it is possible to provide the methods which are
    necessaries so that the QTreeView can visualize the data inside
    the model.

    """
    expand = QtCore.pyqtSignal(QtCore.QModelIndex)
    currentTrackChanged = QtCore.pyqtSignal(object)

    def __init__(self, player, extensions):
        super().__init__()
        self._roots = []
        self._columns_name = ['Filename', 'Size']
        """Track that is currently being played or that it has been
        just stopped."""
        self._currenttrack = None
        self._player = weakref.proxy(player)
        self._extensions = extensions

    def currentTrack(self):
        """Return the current track."""
        if self._currenttrack is not None: rvalue = self._currenttrack
        elif self._roots:
            # Search for a valid track
            for root in self._roots:
                rvalue = root.firstValid()
                if rvalue is not None: self.setCurrentTrack(rvalue) ; break
            else:
                rvalue = None
        else:
            rvalue = None
        return rvalue

    def setCurrentTrack(self, track):
        """Set the current to *track*."""
        self.layoutAboutToBeChanged.emit()
        self._currenttrack = track
        self.currentTrackChanged.emit(self._currenttrack)
        self.layoutChanged.emit()

    def getNextTrack(self):
        """Select the next track as the current track. Return a cuple
        (Track, bool), where the first element is the new current
        Track or None if the pplaylist is empty, while the second
        element defines whether the current track has been obtained by
        cycling the list."""
        if self._currenttrack is None: rvalue = self.currentTrack(), False
        else:
            loop = False
            next = self._getNext(self._currenttrack)
            if next is None:
                loop = True
                self._currenttrack = None
            else:
                self.setCurrentTrack(next)
            rvalue = self.currentTrack(), loop
        return rvalue

    def _getNext(self, element):
        """Returns the first valid Track inside the playlist starting
        the research from the argument tree element.  This function
        starts the research inside the subtrees at the same level of
        'element' and then it searches in the tree at upper level (it
        searches till the roots of the tree)"""
        if element is None: return None
        else:
            parent = element.parent()
            if parent is None:
                next = None
                # The current track is one of the roots, then check the roots
                next_index = self._roots.index(element) + 1
                if next_index<len(self._roots):
                    next = self._roots[next_index].firstValid()
                    if not next is None:
                        return next
                    else:
                        # if there is not an element in the sub tree it is necessary
                        # to search the next subtree
                        next = self._getNext(self._roots[next_index])
                        return next
                else:
                    # It is the last root now way to find a next element.
                    return None
            else:
                # The current track is not one of the roots.
                next = None
                # Start checking the next element at the same level
                next_index = parent.index(element) + 1
                if next_index < parent.size():
                    children = parent.children()
                    next = children[next_index].firstValid()
                    if not next is None:
                        return next
                    else:
                        # if there is not a good element in the sub
                        # tree it is necessary to search the next
                        # subtree
                        next = self._getNext(children[next_index])
                        return next
                else:
                    # It is the last child then it is necessary to find the next
                    # at the parent level
                    next = self._getNext(parent)
                    return next

    def clear(self):
        """Clear the playlist by removing all the tracks."""
        indexes = [] # list of QModelIndex of the root elements
        for i in range(len(self._roots)):
            indexes.append(self.createIndex(i, 0, self._roots[i]))
        self.removeElements(indexes)

    def createFolder(self, name, index=QtCore.QModelIndex(), row=-1):
        """Create an empty folder *name* at *index* and *row*."""
        folder = ListFolder(name)
        if row==-1:
            row = len(self._roots) if not index.isValid() \
                else len(index.internalPointer().children())
        self.insertRows(row, 1, index, [folder])
        # Expand the index if it is a ListFolder
        if index.isValid(): self.expand.emit(index)

    def addElements(self, filepaths, index=QtCore.QModelIndex(), row=-1):
        """Add a list of elements to the playlist."""
        # Create a list of items that will be added to the end of the playlist
        items = []
        for filepath in filepaths:
            # Ensure that it is a string
            filepath = os.path.normpath(str(filepath))
            if os.path.exists(filepath):
                if os.path.isfile(filepath):
                    new_item = self._fileToPlaylist(filepath)
                    if not new_item is None:
                        items.append(new_item)
                elif os.path.isdir(filepath):
                    new_item = self._dirToPlaylist(filepath)
                    if not new_item is None:
                        items.append(new_item)
        if index.isValid():
            # Insert the new elements as the index children
            if row==-1: row = len(index.internalPointer().children())
            self.insertRows(row, len(items), index, items)
        else:
            # Insert the new elements as roots
            if row==-1: row = len(self._roots)
            self.insertRows(row, len(items), index, items)
        # If the current track is not yet defined set, try to determine it
        if self._currenttrack is None: self.currentTrack()
        # Find all the new ListFolder in order to expand them immediately.
        folders = []
        for item in items:
            folders.extend(self._findFolders(item, index, True))
        if index.isValid():
            folders.append(index)
        # Now send expand signals for all of them.
        for folder in folders:
            self.expand.emit(folder)

    def removeElements(self, indexes):
        """ Remove from the playlist all item in *indexes*."""
        # Filter the list of the selected elements since indexes may
        # contain an index for each cell (row & column). In TreeView
        # many cells (the ones on the same row) corresponds to the
        # same TElem then it is better to get the list of the
        # different TElem that have to be removed.
        list = []
        for index in indexes:
            if index.isValid():
                # Retrieve the element
                element = index.internalPointer()
                # Look if the element has already been found.
                found = False
                for item in list:
                    if item['element'] == element:
                        found = True
                        break
                # If not store it and its index
                if not found:
                    item = {'element':element, 'index':index}
                    list.append(item)
        # It is necessary to check if an ancestor of the
        # current track is one of the elements that have been selected
        # and that will be removed
        if not self._currenttrack is None:
            removed = False
            ancestors = self._currenttrack.ancestors()
            ancestors.append(self._currenttrack)
            for ancestor in ancestors:
                for item in list:
                    if item['element']==ancestor: removed = True ; break
            if removed:
                self.setCurrentTrack(None)
        # Now scroll the new list of the element to be removed
        for item in list:
            # Retrieve the parent index
            parent_index = item['index'].parent()
            if not parent_index.isValid():
                # it could be one of the roots
                if self._roots.count(item['element']) > 0:
                    self.removeRow(self._roots.index(item['element']), parent_index)
                else:
                    # If it is not one of the roots, then it is
                    # possible that its parent has already been
                    # removed. This happens when a folder and its
                    # elements are selected. If this method removes
                    # the folder first, then the sub-element won't
                    # have a valid parent
                    pass
            else:
                parent = parent_index.internalPointer()
                child_index = parent.index(item['element'])
                self.removeRow(child_index, parent_index)
        # Check that the current track is set
        self.currentTrack()

    def savePlaylist(self, filepath, index=QtCore.QModelIndex()):
        """ This method save the current playlist to an xml file.
            @param filepath: Path to the file where the playlist will be saved.
            @type filepath: String
            @param parentIndex: index to which the new elements will be attached.
                If None the new items will be attached as roots.
            @type parentIndex: QtCore.QModelIndex
        """
        filepath = os.path.normpath(filepath)
        dirpath, filename = os.path.split(filepath)
        # build a tree structure
        playlist = xmlET.Element("playlist")
        playlist.set("version", "0.1")
        title = xmlET.SubElement(playlist, "title")
        tracklist = xmlET.SubElement(playlist, "tracklist")
        if index.isValid():
            title.text = index.internalPointer().name()
            for child in index.internalPointer().children():
                # Add all the roots to the tracklist element
                element = self._itemPlaylistToXML(child)
                if element is not None:
                    tracklist.append(element)
        else:
            title.text = filename
            for root in self._roots:
                # Add all the roots to the tracklist element
                element = self._itemPlaylistToXML(root)
                if element is not None:
                    tracklist.append(element)

        # wrap it in an ElementTree instance, and save as XML
        document = xmlET.ElementTree(playlist)
        document.write(filepath, 'UTF-8')

    def isValid(self, filepath):
        for accepted in self._extensions:
            if filepath.endswith(accepted): rvalue = True ; break
        else:
            rvalue = False
        return rvalue

    def index(self, row, column, parent_index):
        """Return the index of the item in the model specified by the
           given row, column and parent index."""
        return self.createIndex(row, column, self._roots[row]) \
            if not parent_index.isValid() \
            else self.createIndex(row, column,
                                  parent_index.internalPointer().children()[row])

    def modelIndex(self, element):
        """Return the correspondent QModelIndex for *element*."""
        return self.createIndex(self._roots.index(element), 0, element) \
            if element.parent() is None \
            else self.createIndex(element.parent().index(element), 0, element)

    def parent(self, index):
        """Return the index of the parent of the argument child."""
        if not index.isValid(): rvalue = QtCore.QModelIndex()
        else:
            parent = index.internalPointer().parent()
            if parent is None: rvalue = QtCore.QModelIndex()
            else:
                grandparent = parent.parent()
                if grandparent is None:
                    # The parent could be one of the roots
                    rvalue = QtCore.QModelIndex() if parent not in self._roots \
                        else self.createIndex(self._roots.index(parent), 0,
                                              parent)
                else:
                    # The the index of the parent in the grandparent's children
                    rvalue = self.createIndex(
                        grandparent.children().index(parent), 0, parent)
        return rvalue

    def rowCount(self, index):
        """Return the number of rows (i.e. children) under the *index*."""
        if not index.isValid():
            # Return the number of roots.
            rvalue = len(self._roots)
        else:
            item = index.internalPointer()
            rvalue = len(item.children()) if isinstance(item, TNode) else 0
        return rvalue

    def columnCount(self, parent): return len(self._columns_name)

    def data(self, index, role):
        """ Return the data stored under the given *role* for the item
        referred to by the *index*."""
        if role==QtCore.Qt.TextAlignmentRole:
            rvalue = QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft
        elif role==QtCore.Qt.DecorationRole:
            item = index.internalPointer()
            if isinstance(item, ListFolder) and index.column()==0:
                rvalue = QtGui.QIcon(os.path.join(_config["icons"], 'folder.png'))
            elif isinstance(item, File) and index.column()==0:
                if isinstance(item, Track):
                    if item.valid():
                        rvalue = QtGui.QIcon(os.path.join(_config["icons"],
                                                          'file.png'))
                    else:
                        rvalue = QtGui.QIcon(os.path.join(_config["icons"],
                                                          'file-not_valid.png'))
                else:
                    rvalue = QtGui.QIcon(os.path.join(_config["icons"],
                                                      'file-not_valid.png'))
            else:
                rvalue = None
        elif role==QtCore.Qt.FontRole:
            rvalue = QtGui.QFont()
            item = index.internalPointer()
            if item==self._currenttrack and self._player.isRunning():
                rvalue.setBold(True)
        elif role==QtCore.Qt.ForegroundRole:
            rvalue = QtGui.QBrush()
            # If the item is not valid, print in red color
            item = index.internalPointer()
            if isinstance(item, Track) and not item.valid():
                rvalue.setColor(QtCore.Qt.red)
        elif role==QtCore.Qt.BackgroundRole:
            rvalue = QtGui.QBrush()
            item = index.internalPointer()
            if self._currenttrack==item:
                rvalue.setStyle(QtCore.Qt.SolidPattern)
                rvalue.setColor(QtGui.QColor(190,190,190) \
                    if self._player.isRunning() \
                    else QtGui.QColor(130,130,130))
        elif role!=QtCore.Qt.DisplayRole: rvalue = None
        elif not index.isValid(): rvalue = QtCore.QVariant()
        else:
            item = index.internalPointer()
            if isinstance(item, Track):
                rvalue = item.filename() if index.column()==0 \
                    else '%d bytes'%item.size() if index.column()==1 \
                    else None
            elif isinstance(item, ListFolder):
                rvalue = item.name() if index.column()==0 \
                    else '%d items'%item.size() if index.column()==1 \
                    else None
            else:
                rvalue = 'error'
        return rvalue

    def setData(self, index, value, role):
        """Set the data at *index* to *value* for the specified
        *role*. Return whether the operation has been successfull."""
        rvalue = False
        if index.isValid() and role==QtCore.Qt.EditRole and index.column()==0:
            element = index.internalPointer()
            if isinstance(element, ListFolder):
                element._name = str(value)
                rvalue = True
                self.dataChanged.emit(index, index)
        return rvalue;

    def flags(self, index):
        """Used by other components to obtain information about each
        item provided by the model."""
        # Retrieve the default flags
        flags = QtCore.QAbstractItemModel.flags(self, index)
        if not index.isValid(): rvalue = QtCore.Qt.ItemIsDropEnabled | flags
        else:
            elem = index.internalPointer()
            rvalue = QtCore.Qt.ItemIsDragEnabled | flags \
                if not isinstance(elem, ListFolder) \
                else (QtCore.Qt.ItemIsDragEnabled \
                          | QtCore.Qt.ItemIsDropEnabled \
                          | QtCore.Qt.ItemIsEditable \
                          | flags) \
                if index.column()==0 \
                else (QtCore.Qt.ItemIsDragEnabled \
                          | QtCore.Qt.ItemIsDropEnabled \
                          | flags)
        return rvalue

    def headerData(self, section, orientation, role):
        """This method should return the string that has to be shown
        in the header at a specific index.  For horizontal headers,
        the section number corresponds to the column
        number. Similarly, for vertical headers, the section number
        corresponds to the row number."""
        rvalue = self._columns_name[section] \
            if (orientation==QtCore.Qt.Horizontal \
                    and role==QtCore.Qt.DisplayRole) \
            else ""

    def insertRows(self, position, count, parent_index, rows=None):
        """Inserts *rows* into the model before the *position*. Items
        in the new row will be children of the item represented by the
        parent model index. Return whether the row has been correctly
        insered."""
        self.beginInsertRows(parent_index, position, position+count-1)
        if rows is None: rows = [TElem()]*count
        if not parent_index.isValid():
            # Add rows as roots elements
            self._roots[position:position] = rows
            rvalue = True
        else:
            parent = parent_index.internalPointer()
            if isinstance(parent, ListFolder):
                parent.attachChildren(rows,position)
                rvalue = True
            else:
                rvalue = False
        self.endInsertRows()
        return rvalue

    def removeRow(self, position, parent_index):
        """Removes the row at the given position under the parent at
        parent_index."""
        if not parent_index.isValid():
            self.beginRemoveRows(parent_index, position, position)
            del self._roots[position]
            self.endRemoveRows()
        else:
            parent = parent_index.internalPointer()
            self.beginRemoveRows(parent_index, position, position)
            parent.detachChildAt(position)
            self.endRemoveRows()
        return True

    def removeRows(self, position, count, parent_index):
        """Removes count rows starting with the given row under parent
        parent from the model."""
        if not parent_index.isValid():
            self.beginRemoveRows(parent_index, position, position + count - 1)
            del self._roots[position:position + count]
            self.endRemoveRows()
        else:
            parent = parent_index.internalPointer()
            self.beginRemoveRows(parent_index, position, position + count - 1)
            parent.detachChildrenAt(position, position + count)
            self.endRemoveRows()
        return True

    def supportedDropActions(self): return QtCore.Qt.MoveAction

    class MyMimeData(QtCore.QMimeData):
        def __init__(self, draggedItems):
            super().__init__()
            self.items = draggedItems

        def formats(self):
            """Returns a list of formats supported by the object. This
            is a list of MIME types for which the object can return
            suitable data."""
            return ["boing/player/draggedItems"]

        def hasFormat(self, format):
            """Returns true if the object can return data for the MIME
            type specified by mimeType; otherwise returns false."""
            return format=="boing/player/draggedItems"

        def retrieveData(self, format, type):
            """Returns a variant with the given type containing data
            for the MIME type specified by mimeType. If the object
            does not support the MIME type or variant type given, a
            null variant is returned instead."""
            return self.items if format=="boing/player/draggedItems" \
                else None

    def mimeTypes(self):
        """Returns a list of MIME types that can be used to describe a
        list of model indexes."""
        return ["boing/player/draggedItems"]

    def mimeData(self, indexes):
        """Returns a mimeData object representing the playlist's items
        indexed by 'indexes'."""
        return Playlist.MyMimeData(indexes)

    def dropMimeData(self, data, action, row, column, newParentIndex):
        """ This method is invoked when playlist's items are dragged
        and dropped."""
        raw_indexes = data.retrieveData("boing/player/draggedItems", None)
        # Filter the indexes to keep only the indexes to the first column
        indexes = []
        for currIndex in raw_indexes:
            if currIndex.column() == 0:
                indexes.append(currIndex)
        if len(indexes) == 0: rvalue = False
        else:
            newParent = newParentIndex.internalPointer()
            # If items are added to an empty folder, expand it
            if not newParent is None:
                if len(newParent.children()) == 0:
                    newParent._expanded = True
            # Filter the indexes so that there are not toMove and
            # children together. toMove is a dict that has
            # QModelIndex for keys, and a list of QModelIndex for
            # values. The items that have been dropped are listed as
            # values where the keys is the common parent.
            toMove = {}
            for currIndex in indexes:
                currItem = currIndex.internalPointer()
                # Check if in toMove there is already an ancestor of
                # the currItem
                found_ancestor = False
                for addedItemIndexes in toMove.values():
                    for addedItemIndex in addedItemIndexes:
                        if currItem.hasAncestor(addedItemIndex.internalPointer()):
                            found_ancestor = True
                            break
                    if found_ancestor: break
                if found_ancestor:
                    # If an ancestor has been already added then it is
                    # not necessary to consider this element
                    break
                else:
                    # Else it is possible to add the new Item.
                    if isinstance(currItem, ListFolder):
                        # If the new item is a folder check if it is
                        # an ancestor of elements that have been
                        # already added.
                        toRemove = []
                        for oldParentIndex in toMove.keys():
                             if oldParentIndex.isValid() and \
                                     (oldParentIndex.internalPointer().hasAncestor(currItem) \
                                          or oldParentIndex.internalPointer()==currItem):
                                 toRemove.append(oldParentIndex)
                        # Remove all the toMove that have the new item
                        # as ancestor.
                        for remove in toRemove:
                            del toMove[remove]
                    # The currIndex is added
                    if currIndex.parent() in toMove:
                        # If the oldParentIndex is already in append the new item
                        toMove[currIndex.parent()].append(currIndex)
                    else:
                        toMove[currIndex.parent()] = [currIndex]
            # Reverse all the lists
            for items in toMove.values():
                items.reverse()
            # --- Now it is possible to move the the filtered indexes ---
            for oldParentIndex, children in toMove.items():
                for child_index in children:
                    child = child_index.internalPointer()
                    if oldParentIndex.isValid():
                        oldPos = \
                            oldParentIndex.internalPointer().children().index(child)
                    else:
                        oldPos = self._roots.index(child)
                    if row==-1:
                        row = len(self._roots) if newParent is None \
                            else len(newParent.children())
                    if oldParentIndex==newParentIndex and oldPos<row:
                        row -= 1
                    self.removeRow(oldPos, oldParentIndex)
                    self.insertRows(row, 1, newParentIndex, [child])
            # Since indexes changes it is necessary to expand the folders which
            # were expanded.
            folders = []
            for root in self._roots:
                folders.extend(self._findFolders(root, QtCore.QModelIndex(), True))
            # Send expand signals for all of them
            for folder in folders:
                if folder.internalPointer().expanded():
                    self.expand.emit(folder)
            rvalue = True
        return rvalue

    def _findFolders(self, element, parent_index, notEmpty=False):
        """Return all the QModelIndex of the ListFolders inside the
        current element or inside its children."""
        if element is None:
            return []
        elif not isinstance(element, ListFolder):
            return []
        else:
            if len(element.children())==0 and notEmpty:
                # if the empty folders are not requested..
                return []
            else:
                element_index = None
                if not parent_index.isValid():
                    if self._roots.count(element) > 0:
                        row = self._roots.index(element)
                        element_index = self.index(row, 0, parent_index)
                    else:
                        return []
                else:
                    parent = parent_index.internalPointer()
                    row = parent.index(element)
                    element_index = self.index(row, 0, parent_index)
                folders = [element_index]
                for child in element.children():
                    folders.extend(self._findFolders(child, element_index))
                return folders

    def onItemExpanded(self, index):
        item = index.internalPointer()
        if isinstance(item, ListFolder): item._expanded = True

    def onItemCollapsed(self, index):
        item = index.internalPointer()
        if isinstance(item, ListFolder): item._expanded = False

    # <<<<<<<<<<<<<<<<<<< MODEL CONVERSION PRIVATE METHODS >>>>>>>>>>>>>>>>>>>>
    def _fileToPlaylist(self, filepath):
        """ This method is invoked when any file (not directories) is going to
            be insered into the playlist.
            @param filepath: the filesystem path to that file
            @type filepath: string
            @return: a new Track or ListFolder or None
            @rtype: Track or ListFolder or None
        """
        # If the file has the playlist extension
        if filepath[(len(filepath) - 4):] == ('.' + EXTENSION):
            # load the playlist
            return self._playlistFileToPlaylist(filepath)
        else:
            return Track(filepath, self.isValid(filepath))

    def _dirToPlaylist(self, filepath):
        """ This method is invoked when a filesystem directory is going to be 
            insered into the playlist.
            @param filepath: the filesystem path to that directory
            @type filepath: string
            @return: a new ListFolder or None
            @rtype: ListFolder or None
        """
        # split the dirpath and the filename
        dirpath, filename = os.path.split(filepath)
        listFolder = ListFolder(filename)
        if os.path.isdir(filepath):
            # Convert also the internal structure of the filesystem folder            
            ls = os.listdir(filepath)
            for entry in ls:
                entry_path = '%s/%s'%(filepath, entry)
                if os.path.isfile(entry_path):
                    # if it is a file
                    subTrack = self._fileToPlaylist(entry_path)
                    if not subTrack is None:
                        listFolder.attachChild(subTrack)
                elif os.path.isdir(entry_path):
                    # if it is a directory
                    subListFolder = self._dirToPlaylist(entry_path)
                    if not subListFolder is None:
                        listFolder.attachChild(subListFolder)       
        return listFolder    
        
    
    def _playlistFileToPlaylist(self, filepath):
        """ This method is invoked when a stored playlist is going to be 
            imported into the playlist.            
            @param filepath: the filesystem path to the playlist file
            @type filepath: string
            @return: a new ListFolder or None
            @rtype: ListFolder or None
        """
        listFolder = None
        # Generate the xml tree
        tree = xmlET.parse(filepath)        
        # get the root element
        root = tree.getroot()        
        if not root is None:
            
            # Retrieve the playlist name
            title = root.find('title')                        
            if title is None:
                title = 'unnamed'
            else:
                title = title.text
                                
            tracklist = root.find('tracklist')                        
            if not tracklist is None:                
                # --- Construct the tree playlist from the xml elements ---
                listFolder = ListFolder(title)
                # Scroll all the internal elements
                for element in tracklist:
                    item = self._elemXmlToPlaylist(element)
                    if not item is None:
                        listFolder.attachChild(item)
                                     
        return listFolder         

    def _itemPlaylistToXML(self, element):
        """ This recursive private method is used to convert the playlist elements
            into xml elements.
            @param element: the playlist element that has to be placed into the
                xml structure.
            @type element: Track or ListFolder
            @return: the xml element correspondent to the given playlist element.
            @rtype: xml.etree.ElementTree.Element or None
        """
        if isinstance(element, Track):
            # Add the single track
            track = xmlET.Element("track")
            location = xmlET.SubElement(track, "location")
            location.text = element.filepath()
            return track
        elif isinstance(element, ListFolder):
            # Add the folder element and also all its children
            folder = xmlET.Element("folder")
            name = xmlET.SubElement(folder, "name")
            name.text = element.name()
            for child in element.children():
                element = self._itemPlaylistToXML(child)
                if not element is None :
                    folder.append(element)
            return folder
        else:
            return None

    def _elemXmlToPlaylist(self, element):
        """ This recursive private method takes as argument an Element of the
            xml tree and it creates a correspondent branch of TElem.
            @param element: The element retrieved from the xml file.
            @type  element: xml.etree.ElementTree.Element
            @return: the translation of element in a Track or ListFolder item
            @rtype: Track or ListFolder or None 
        """
        if element.tag == 'track':
            # If the element is a track...
            location = element.find('location')
            if not location is None:
                # create a new Track with the correspondent location.
                return Track(location.text, self.isValid(location.text))
        elif element.tag == 'folder':
            # If the element is a folder...
            item = None
            name = element.find('name')
            if name is None:
                # create a new Listfolder unnamed.
                item = ListFolder('unnamed')
            else:
                # create a new Track with the correspondent name.
                item = ListFolder(name.text)
            for subelement in element:
                # Scroll all the sub elements.
                subitem = self._elemXmlToPlaylist(subelement)
                if not subitem is None:
                    item.attachChild(subitem)
            return item
        else:
            return None
