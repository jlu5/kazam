#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       app.py
#       
#       Copyright 2010 Andrew <andrew@karmic-desktop>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
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

import locale
import gettext
import logging
import gtk
import os

from SimpleGtkbuilderApp import SimpleGtkbuilderApp
from gettext import gettext as _

from window_start import *
from window_countdown import CountdownWindow
from indicator import KazamIndicator

class KazamApp(SimpleGtkbuilderApp):

    def __init__(self, datadir):
    
        self.datadir = datadir
        SimpleGtkbuilderApp.__init__(self, 
                                     os.path.join(datadir, "ui/kazam.ui"),
                                     "kazam")
        gettext.bindtextdomain("kazam", "/usr/share/locale")
        gettext.textdomain("kazam")

        try:
            locale.setlocale(locale.LC_ALL, "")
        except:
            logging.exception("setlocale failed")
        
        try:
            locale.setlocale(locale.LC_ALL, "")
        except Exception, e:
            logging.exception("setlocale failed")
    
        self.icons = gtk.icon_theme_get_default()
        self.icons.append_search_path(os.path.join(datadir,"icons","22x22","status"))
        gtk.window_set_default_icon_name("kazam")
        
        populate_combobox_video(self.combobox_video)
        populate_combobox_audio(self.combobox_audio)

    # Callbacks
    def on_checkbutton_video_toggled(self, checkbutton_video):
        self.combobox_video.set_sensitive(checkbutton_video.get_active())
    def on_checkbutton_audio_toggled(self, checkbutton_audio):
        self.combobox_audio.set_sensitive(checkbutton_audio.get_active())
    def on_menuitem_quit_activate(self, checkbutton_audio):
        gtk.main_quit()
    def on_window_start_delete_event(self, window, event):
        gtk.main_quit()
    def on_button_close_clicked(self, button_close):
        gtk.main_quit()
    def on_button_record_clicked(self, button_record):
        self.window_start.hide()
        self.window_countdown = CountdownWindow()
        self.indicator = KazamIndicator(self.icons)
        self.window_countdown.connect("count", self.on_window_countdown_count)
        self.window_countdown.connect("done", self.on_window_countdown_done)
    def on_window_countdown_count(self, window_countdown):
        self.indicator.count(window_countdown.number)
    def on_window_countdown_done(self, window_countdown):
        self.indicator.start_recording()
        print "Let's go!"
    # Functions

    def run(self):
        self.window_start.show_all()
        SimpleGtkbuilderApp.run(self)



