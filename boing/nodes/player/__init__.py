# -*- coding: utf-8 -*-
#
# boing/nodes/player/__init__.py -
#
# Author: Paolo Olivo (paolo.olivo@inria.fr)
#
# Copyright © INRIA
#
# See the file LICENSE for information on usage and redistribution of
# this file, and for a DISCLAIMER OF ALL WARRANTIES.

import os.path

TEXTUREPATH = os.path.join(os.path.dirname(__file__), 'icons')

EXTENSION = 'bpl'
"""File extension used when saving playlists to file."""

PLAYONE, LOOPONE, PLAYALL, LOOPALL = (object() for i in range(4))
MODALITIES = [PLAYONE, LOOPONE, PLAYALL, LOOPALL]
"""Available modalities:

PLAYONE - Play one single track and move to the next one.

LOOPONE - Loop over one single track.

PLAYALL - Play until the end of the playlist.

LOOPALL - Loop over the entire playlist.
"""

from boing.core import Offer
from boing.nodes.logger import FilePlayer
from boing.nodes.player import gui, playlist

class Player(FilePlayer):
    """The Player class defines a producer node that can play log
    files. The Player owns a playlist of files and a graphical user
    interface for similar to other music players."""
    def __init__(self, decoder, sender, extensions=("",), open=tuple(),
                 speed=1, interval=0,
                 offer=Offer(Offer.UndefinedProduct()), parent=None):
        super().__init__(None, decoder, sender, interval=interval,
                         offer=offer, parent=None)
        self._mode = PLAYALL
        self._playlist = playlist.Playlist(self, extensions)
        self._playlist.currentTrackChanged.connect(self._currentTrackChanged)
        self._gui = gui.PlayerWidget(self._playlist)
        self._gui.nextMode.connect(self.nextMode)
        self._gui.setSpeed.connect(self.setSpeed)
        self.started.connect(self._gui.started)
        self.stopped.connect(self._gui.stopped)
        self._gui.playFile.connect(self.play)
        self._gui.togglePlayStop.connect(self.toggleStartStop)
        if open: self._playlist.addElements(open.split(":"))

    def gui(self): return self._gui
    def mode(self): return self._mode

    def nextMode(self):
        index = MODALITIES.index(self.mode())
        self._mode = MODALITIES[(index+1)%len(MODALITIES)]
        self._gui.modeChanged(self.mode())

    def toggleStartStop(self):
        if self.isRunning():
            self.stop()
        elif self.file() is not None:
            self.start()
        else:
            track = self._playlist.currentTrack()
            if track is not None: self.play(track.filepath())

    def _finished(self):
        self._parser.reset()
        if self.mode()==PLAYONE:
            track, loop = self._playlist.getNextTrack()
            self.stop()
        elif self.mode()==PLAYALL:
            track, loop = self._playlist.getNextTrack()
            if not loop:
                self._waittimer.start(self.interval())
            else:
                self.stop()
        elif self.mode()==LOOPONE:
            self._waittimer.start(self.interval())
        elif self.mode()==LOOPALL:
            track, loop = self._playlist.getNextTrack()
            if track is not None:
                self._waittimer.start(self.interval())
            else:
                self.stop()

    def _currentTrackChanged(self, track):
        if track is None: self.stop()
        self.setFile(track if track is None else track.filepath())
