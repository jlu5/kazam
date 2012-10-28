# -*- coding: utf-8 -*-
#
#       prefs.py
#
#       Copyright 2012 David Klasinc <bigwhale@lubica.net>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.

import os
import logging
from gettext import gettext as _
from xdg.BaseDirectory import xdg_config_home

class Prefs():
    def __init__(self):
        """Initialize prefs and set all the preference variables to their
           default values.

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self.logger = logging.getLogger("Prefs")

        #
        # GUI preferences and stuff
        #
        self.capture_cursor = False
        self.capture_speakers = False
        self.capture_microphone = False

        self.capture_cursor_pic = False

        self.countdown_timer = 5

        self.speakers_source = None
        self.microphone_source = None

        self.speakers_volume = 0
        self.microphone_volume = 0

        self.countdown_splash = True
        self.silent_start = False

        #
        # Other stuff
        #
        self.datadir = None

        #
        # Capture related stuff
        #
        self.codec = None
        self.pa_q = None
        self.framerate = 15
        self.autosave_video = False
        self.autosave_video_file = None

        self.autosave_picture = False
        self.autosave_picture_file = None
        self.shutter_sound = True
        self.shutter_type = 0
        self.shutter_sound_file = ""

        self.area = None
        self.xid = None

        #
        # Audio sources
        #  - Tuple of all sources
        #  - Selected first source
        #  - Selected second source
        #
        self.audio_sources = None
        self.audio_source = None
        self.audio2_source = None

        #
        # Command line parameters
        #
        self.debug = False
        self.test = False
        self.dist = ('Ubuntu', '12.10', 'quantal')
        self.silent = False
        self.sound = True

        self.get_dirs()

    def get_audio_sources(self):
        self.logger.debug("Getting Audio sources.")
        try:
            self.audio_sources = prefs.pa_q.get_audio_sources()
            #self.audio_sources.insert(0, [])
            if prefs.debug:
                for src in self.audio_sources:
                    self.logger.debug(" Device found: ")
                    for item in src:
                        self.logger.debug("  - {0}".format(item))
        except:
            # Something went wrong, just fallback to no-sound
            self.logger.warning("Unable to find any audio devices.")
            self.audio_sources = [[0, _("Unknown"), _("Unknown")]]

    def get_dirs(self):
        paths = {}
        f = None
        try:
            f = open(os.path.join(xdg_config_home, "user-dirs.dirs"))
            for la in f:
                if la.startswith("XDG_VIDEOS") or la.startswith("XDG_DOCUMENTS") or la.startswith("XDG_PICTURES") :
                    (idx, val) = la.strip()[:-1].split('="')
                    paths[idx] = os.path.expandvars(val)
        except:
            paths['XDG_VIDEOS_DIR'] = os.path.expanduser("~/Videos/")
            paths['XDG_PICTURES_DIR'] = os.path.expanduser("~/Pictures/")
            paths['XDG_DOCUMENTS_DIR'] = os.path.expanduser("~/Documents/")
        finally:
            if f is not None:
                f.close()

        paths['HOME_DIR'] = os.path.expandvars("$HOME")

        if os.path.isdir(paths['XDG_VIDEOS_DIR']):
            self.video_dest = paths['XDG_VIDEOS_DIR']
        elif os.path.isdir(paths['XDG_DOCUMENTS_DIR']):
            self.video_dest = paths['XDG_DOCUMENTS_DIR']
        elif os.path.isdir(paths['HOME_DIR']):
            self.video_dest = paths['HOME_DIR']

        if os.path.isdir(paths['XDG_PICTURES_DIR']):
            self.picture_dest = paths['XDG_PICTURES_DIR']
        elif os.path.isdir(paths['XDG_DOCUMENTS_DIR']):
            self.picture_dest = paths['XDG_DOCUMENTS_DIR']
        elif os.path.isdir(paths['HOME_DIR']):
            self.picture_dest = paths['HOME_DIR']


    def get_sound_files(self):
        self.sound_files = []
        for root, dir, files in os.walk(os.path.join(self.datadir, "sounds")):
            for file in files:
                if file.endswith('.ogg'):
                    self.sound_files.append(file)


prefs = Prefs()
