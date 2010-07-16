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
import shutil

from subprocess import Popen
from SimpleGtkbuilderApp import SimpleGtkbuilderApp
from gettext import gettext as _

from dialogs import *
from window_countdown import CountdownWindow
from indicator import KazamIndicator
from recording import Recording
from done_recording import DoneRecording
from start_recording import RecordingStart

class KazamApp(SimpleGtkbuilderApp):

    def __init__(self, datadir):
    
        self.datadir = datadir
        SimpleGtkbuilderApp.__init__(self, 
                                     os.path.join(datadir, "ui", "start.ui"),
                                     "kazam")
        gettext.bindtextdomain("kazam", "/usr/share/locale")
        gettext.textdomain("kazam")
        
        try:
            locale.setlocale(locale.LC_ALL, "")
        except Exception, e:
            logging.exception("setlocale failed")
    
        self.icons = gtk.icon_theme_get_default()
        self.icons.append_search_path(os.path.join(datadir,"icons","22x22","status"))
        gtk.window_set_default_icon_name("kazam")
        
        # Will be set later, here for convenience
        self.window_countdown = None
        self.indicator = None
        self.done_recording = None
        
        # Let's start!
        self.recording_start = RecordingStart(self.datadir)
        self.recording_start.connect("countdown-requested", self.cb_countdown_requested)
        
    # Callbacks
        
    def on_window_countdown_count(self, window_countdown):
        self.indicator.count(window_countdown.number)
        
    def on_indicator_recording_done(self, indicator):
        self.recording.stop()
        self.done_recording = DoneRecording(self.datadir, self.icons)
        self.done_recording.connect("save-requested", self.cb_save_requested)
        self.done_recording.connect("edit-requested", self.cb_edit_requested)
        self.done_recording.run()
        
    def cb_record_requested(self, window_countdown):
        self.indicator.start_recording()
        self.recording = Recording()
        
    def cb_countdown_requested(self, recording_start):
        audio = recording_start.checkbutton_audio.get_active()
        del recording_start
        
        self.window_countdown = CountdownWindow()
        self.window_countdown.connect("count", self.on_window_countdown_count)
        self.window_countdown.connect("record-requested", self.cb_record_requested)
        self.window_countdown.run_countdown()
        
        self.indicator = KazamIndicator()
        self.indicator.connect("recording-done", self.on_indicator_recording_done)    
        
    def cb_edit_requested(self, done_recording, data):
        (desktop_entry, args_list) = data
        
        command = desktop_entry.getExec()
        args_list.insert(0, desktop_entry.getExec())
        args_list.append(self.recording.get_filename())
        
        Popen(args_list)
        # TODO: make it quit
        gtk.main_quit()
        
    def cb_save_requested(self, done_recording):
        (save_dialog, result) = new_save_dialog("Save screencast", self.done_recording.dialog)
        ## TODO: save properly
        if result == gtk.RESPONSE_OK:
            uri = os.path.join(save_dialog.get_current_folder(), save_dialog.get_filename())
            if not uri.endswith(".mkv"):
                uri += ".mkv"
            shutil.move(self.recording.get_filename(), uri)
        save_dialog.destroy()
        gtk.main_quit()
            
        
    # Functions

    def run(self):
        self.recording_start.run()
        SimpleGtkbuilderApp.run(self)



