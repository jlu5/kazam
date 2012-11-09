#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       instant.py
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

import sys
import logging
from gettext import gettext as _
from gi.repository import Gtk, GObject

from kazam.utils import *
from kazam.backend.prefs import *
from kazam.backend.constants import *
from kazam.backend.grabber import Grabber

logger = logging.getLogger("Instant")

class InstantApp(GObject.GObject):

    def __init__(self, datadir, dist, debug, mode):
        GObject.GObject.__init__(self)
        logger.debug("Setting variables.{0}".format(datadir))

        prefs.datadir = datadir
        prefs.debug = debug
        prefs.dist = dist
        prefs.get_sound_files()

        self.old_path = None

        if HW.combined_screen:
            self.video_source = HW.combined_screen
        else:
            screen = HW.get_current_screen(self.window)
            self.video_source = HW.screens[screen]

        self.grabber = Grabber()
        self.grabber.connect("flush-done", self.cb_flush_done)
        self.grabber.connect("save-done", self.cb_save_done)

        if mode == MODE_AREA:
            logger.debug("Area ON.")
            from kazam.frontend.window_area import AreaWindow
            self.area_window = AreaWindow()
            self.area_window.connect("area-selected", self.cb_area_selected)
            self.area_window.connect("area-canceled", self.cb_area_canceled)
            self.area_window.window.show_all()
        elif mode == MODE_ALL:
            self.grabber.setup_sources(self.video_source, None, None)
            logger.debug("Grabbing screen")
            self.grabber.grab()
        elif mode == MODE_ACTIVE:
            self.grabber.setup_sources(self.video_source, None, None, active=True)
            logger.debug("Grabbing screen")
            self.grabber.grab()
        else:
            sys.exit(0)

    def cb_area_selected(self, widget):
        logger.debug("Area selected: SX: {0}, SY: {1}, EX: {2}, EY: {3}".format(
            self.area_window.startx,
            self.area_window.starty,
            self.area_window.endx,
            self.area_window.endy))
        prefs.area = (self.area_window.startx,
                      self.area_window.starty,
                      self.area_window.endx,
                      self.area_window.endy,
                      self.area_window.width,
                      self.area_window.height)
        self.grabber.setup_sources(self.video_source, prefs.area, None)
        logger.debug("Grabbing screen")
        self.grabber.grab()

    def cb_area_canceled(self, widget):
        Gtk.main_quit()
        sys.exit(0)

    def cb_flush_done(self, widget):
        if prefs.autosave_picture:
            fname = get_next_filename(prefs.picture_dest, prefs.autosave_picture_file, ".png")
            self.grabber.autosave(fname)
        else:
            self.grabber.save_capture(None)

    def cb_save_done(self, widget, result):
        logger.debug("Save Done, result: {0}".format(result))
        self.old_path = result

        Gtk.main_quit()
        sys.exit(0)
