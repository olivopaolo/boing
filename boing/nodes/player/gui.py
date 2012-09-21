# -*- coding: utf-8 -*-
#
# boing/nodes/player/gui.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import os.path

from PyQt4 import QtCore, QtGui, uic

from boing.nodes.player import \
    TEXTUREPATH, EXTENSION, \
    PLAYONE, LOOPONE, PLAYALL, LOOPALL
from boing.nodes.player.playlist import Track, ListFolder

from boing.nodes.player.uiPlayer import Ui_player

class PlayerWidget(QtGui.QMainWindow, Ui_player):
    """This class defines the PlaylistPlayer main widget."""

    playFile = QtCore.pyqtSignal(str)
    togglePlayStop = QtCore.pyqtSignal()
    nextMode = QtCore.pyqtSignal()
    setSpeed = QtCore.pyqtSignal(float)
    closed = QtCore.pyqtSignal()
    """Emitted when the Widget is closed."""

    def __init__(self, playlist, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self._playlistview = PlaylistView(playlist)
        self._playlistview.doubleClicked.connect(self.playSelection)
        self._playlistview.playFile.connect(self.playFile)
        self._frame.layout().addWidget(self._playlistview)
        # Context menu
        menu = QtGui.QMenu()
        menu.addAction("Play", self.playSelection, QtCore.Qt.Key_Enter)
        menu.addAction("Delete", self.deleteSelection, QtCore.Qt.Key_Delete)
        menu.addSeparator()
        menu.addAction('Add File...', self._openFilesDialog)
        menu.addAction('Add Directory...', self._openDirDialog)
        menu.addAction('Import Playlist...', self._importPlaylistDialog)
        menu.addAction('Create folder', self._createFolder)
        menu.addSeparator()
        menu.addAction("Rename", self._playlistview._openEditor)
        self._playlistview.menu = menu
        # playstop button
        self._playstop.clicked.connect(self.togglePlayStop)
        self._playstop.setIcon(QtGui.QIcon(os.path.join(TEXTUREPATH, "play.png")))
        self._playstop.setIconSize(QtCore.QSize(32,32))
        self._togglemode.clicked.connect(self.nextMode)
        # Speed slider
        self._playerspeeds = (
            dict(str="1/16x", value=1/16),
            dict(str="1/8x", value=1/8),
            dict(str="1/4x", value=1/4),
            dict(str="1/2x", value=1/2),
            dict(str="1x", value=1),
            dict(str="2x", value=2),
            dict(str="4x", value=4),
            dict(str="8x", value=8),
            dict(str="16x", value=16),
            )
        self._speedslider.setRange(0, len(self._playerspeeds) - 1)
        self._speedslider.valueChanged.connect(self._sliderChange)
        for i, speed in enumerate(self._playerspeeds):
            if speed['value']==1: self._speedslider.setValue(i) ; break
        # Status bar
        self.statusBar().showMessage('Ready')
        # Menu bar
        self._openfiles.triggered.connect(self._openFilesDialog)
        self._opendir.triggered.connect(self._openDirDialog)
        self._importplaylist.triggered.connect(self._importPlaylistDialog)
        self._saveplaylist.triggered.connect(self._savePlaylistDialog)
        self._createfolder.triggered.connect(self._createFolder)
        self._clear.triggered.connect(self._playlistview.model().clear)
        self._quit.triggered.connect(QtGui.QApplication.instance().quit)
        self._faster.triggered.connect(self.incrementSpeed)
        self._slower.triggered.connect(self.decrementSpeed)
        # Shortcuts
        QtGui.QShortcut(QtCore.Qt.Key_Escape, self,
                        self._playlistview.clearSelection)
        QtGui.QShortcut(QtCore.Qt.Key_Delete, self, self.deleteSelection)

    def _sliderChange(self, value):
        """The 'speedslider' has been moved to *value*."""
        self.setSpeed.emit(self._playerspeeds[value]['value'])
        self._speedlabel.setText(self._playerspeeds[value]['str'])

    def incrementSpeed(self):
        """Increment the speedSlider of one step."""
        if self._speedslider.value()<self._speedslider.maximum():
            self._speedslider.setValue(
                self._speedslider.value()+self._speedslider.singleStep())

    def decrementSpeed(self):
        """Decrement the speedSlider of one step."""
        if self._speedslider.value()>self._speedslider.minimum():
            self._speedslider.setValue(
                self._speedslider.value()-self._speedslider.singleStep())

    def _openFilesDialog(self):
        """Execute a QFileDialog to load files into the playlist."""
        dialog = QtGui.QFileDialog(self)
        dialog.setFileMode(QtGui.QFileDialog.ExistingFiles)
        dialog.setViewMode(QtGui.QFileDialog.List) # or Detail
        if dialog.exec_():
            self._playlistview.addElements(dialog.selectedFiles())

    def _openDirDialog(self):
        """Execute a QFileDialog to load directories into the
        playlist."""
        dialog = QtGui.QFileDialog(self)
        dialog.setFileMode(QtGui.QFileDialog.DirectoryOnly)
        dialog.setViewMode(QtGui.QFileDialog.List) # or Detail
        if dialog.exec_():
            self._playlistview.addElements(dialog.selectedFiles())

    def _importPlaylistDialog(self):
        """Execute QFileDialog to import a playlist file."""
        dialog = QtGui.QFileDialog(self)
        dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        dialog.setViewMode(QtGui.QFileDialog.List) # or Detail
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptOpen)
        # Set filter extension
        dialog.setNameFilter('*.%s'%EXTENSION)
        if dialog.exec_():
            self._playlistview.addElements(dialog.selectedFiles())

    def _savePlaylistDialog(self):
        """Execute a QFileDialog to select a file where the playlist
        will be saved."""
        dialog = QtGui.QFileDialog(self)
        dialog.setFileMode(QtGui.QFileDialog.AnyFile)
        dialog.setViewMode(QtGui.QFileDialog.List) # or Detail
        dialog.setAcceptMode(QtGui.QFileDialog.AcceptSave)
        # Set filter
        dialog.setNameFilter("*.%s"%EXTENSION)
        if dialog.exec_():
            filepath = str(dialog.selectedFiles()[0])
            # Check if the file has the playlist_ext
            if not filepath.endswith(".%s"%EXTENSION):
                filepath += ".%s"%EXTENSION
            self._playlistview.model().savePlaylist(filepath)

    def _createFolder(self):
        """Add an empty folder."""
        self._playlistview.createFolder("New folder")

    def playSelection(self):
        """Start playing the first element of the current
        selection."""
        selection = self._playlistview.selectedIndexes()
        for index in selection:
            track = index.internalPointer().firstValid()
            if track is not None:
                self._playlistview.model().setCurrentTrack(track)
                self.playFile.emit(track.filepath())
                break

    def deleteSelection(self):
        """Delete the selected items."""
        self._playlistview.model().removeElements(
            self._playlistview.selectedIndexes())

    def modeChanged(self, mode):
        """The playlist scroll Mode has changed."""
        if mode is PLAYONE:
            self._togglemode.setText('Play One')
            self.statusBar().showMessage('Play once one single track')
        elif mode is PLAYALL:
            self._togglemode.setText('Play All')
            self.statusBar().showMessage('Play once the entire playlist')
        elif mode is LOOPONE:
            self._togglemode.setText('Loop One')
            self.statusBar().showMessage('Loop over a single track')
        elif mode is LOOPALL:
            self._togglemode.setText('Loop All')
            self.statusBar().showMessage('Loop over the entire playlist')

    def started(self):
        """Update GUI since the player has been started."""
        self._playstop.setIcon(
            QtGui.QIcon(os.path.join(TEXTUREPATH, 'stop.png')))
        self._playstop.setToolTip('Stop playback')
        track = self._playlistview.model().currentTrack()
        self._playlistview.scrollTo(
            self._playlistview.model().modelIndex(track))
        self._playlistview.model().layoutChanged.emit()

    def stopped(self):
        """Update GUI since the player has been stopped."""
        self._playstop.setIcon(
            QtGui.QIcon(os.path.join(TEXTUREPATH, 'play.png')))
        self._playstop.setToolTip('Start playback')
        track = self._playlistview.model().currentTrack()
        self._playlistview.scrollTo(
            self._playlistview.model().modelIndex(track))
        self._playlistview.model().layoutChanged.emit()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)


class PlaylistView(QtGui.QTreeView):
    """Widget for displaying the playlist."""

    playFile = QtCore.pyqtSignal(str)

    def __init__(self, playlist, parent=None):
        super().__init__(parent=parent)
        self.setModel(playlist)
        playlist.currentTrackChanged.connect(self.currentTrackChanged)
        self.setAlternatingRowColors(True)
        self.setIndentation(15)
        self.setUniformRowHeights(True)
        self.setEditTriggers(QtGui.QAbstractItemView.EditKeyPressed)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtGui.QAbstractItemView.InternalMove)
        self.setAutoExpandDelay(1000)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setExpandsOnDoubleClick(False)
        self.setColumnWidth(0, 300)
        playlist.expand.connect(self.expand)

    def keyPressEvent(self, event):
        handled = False
        if event.key()==QtCore.Qt.Key_Return \
                and self.state()!=QtGui.QAbstractItemView.EditingState:
            selection = self.selectedIndexes()
            if selection:
                track = selection[0].internalPointer().firstValid()
                if track is not None:
                    self.model().setCurrentTrack(track)
                    self.playFile.emit(track.filepath())
            handled = True
        if not handled: super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        """Display the context menu."""
        selection = self.selectionModel().selectedRows()
        actions = self.menu.actions()
        if not selection:
            actions[0].setEnabled(False)
            actions[1].setEnabled(False)
            actions[8].setEnabled(False)
        elif len(selection)==1:
            l = lambda index: index.internalPointer().firstValid() is not None
            actions[0].setEnabled(any(map(l, selection)))
            actions[1].setEnabled(True)
            actions[8].setEnabled(isinstance(selection[0].internalPointer(),
                                             ListFolder))
        else:
            l = lambda index: index.internalPointer().firstValid() is not None
            actions[0].setEnabled(any(map(l, selection)))
            actions[1].setEnabled(True)
            actions[8].setEnabled(False)
        self.menu.exec_(event.globalPos())

    def _openEditor(self):
        """ Open the editor over the current selected row if any. """
        rows = self.selectionModel().selectedRows()
        if len(rows)==1: self.edit(rows[0])

    def addElements(self, filepaths):
        """Add the list of *filepaths* to the playlist considering the
        current selection."""
        selection = self.selectionModel().selectedRows()
        if not selection: self.model().addElements(filepaths)
        else:
            last = selection[-1]
            if isinstance(last.internalPointer(), ListFolder):
                # Add files at the end of the selected folder
                self.model().addElements(filepaths, last)
            else:
                # Add files after the last selected track
                self.model().addElements(filepaths, last.parent(), last.row()+1)

    def createFolder(self, name):
        """Create the folder *name* to the playlist considering the
        current selection."""
        selection = self.selectionModel().selectedRows()
        if not selection: self.model().createFolder(name)
        else:
            last = selection[-1]
            if isinstance(last.internalPointer(), ListFolder):
                # Add files at the end of the selected folder
                self.model().createFolder(name, last)
            else:
                # Add files after the last selected track
                self.model().createFolder(name, last.parent(), last.row()+1)

    def dragEnterEvent(self, event):
        """Accept dragged items if they have urls."""
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event):
        """Emit the signal "dropped" if the dragged elements have been
        accepted."""
        if event.mimeData().hasUrls():
            # If mimeData has Urls then some files are being dragged
            # over the playlist and they will be added at bottom.
            links = []
            for url in event.mimeData().urls():
                links.append(str(url.toLocalFile()))
            if links:
                event.setDropAction(QtCore.Qt.CopyAction)
                event.accept()
                self.model().addElements(links)
                self.activateWindow()
        else:
            super().dropEvent(event)

    def currentTrackChanged(self):
        track = self.model().currentTrack()
        self.scrollTo(self.model().modelIndex(track))

    # def _deselectDescent(self, index):
    #     """This method removes from the actual selection all the
    #     descent of the specified index and the index itself."""
    #     if index.isValid():
    #         selectionModel = self.selectionModel()
    #         if selectionModel.isSelected(index):
    #             selectionModel.select(QtGui.QItemSelection(index, index.sibling(index.row(), self.model().columnCount(index)-1)), QtGui.QItemSelectionModel.Deselect)
    #         item = index.internalPointer()
    #         if isinstance(item, TNode):
    #             for row in range(len(item.children())):
    #                 self._deselectDescent(self.model().index(row, 0, index))
