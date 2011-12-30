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

from kazam.backend.config import KazamConfig
from kazam.frontend.widgets.dialogs import new_save_dialog
from kazam.frontend.window_countdown import CountdownWindow
from kazam.frontend.indicator import KazamIndicator
from kazam.frontend.done_recording import DoneRecording
from kazam.frontend.start_recording import RecordingStart
from kazam.frontend.export import ExportFrontend

class KazamApp(object):

    def __init__(self, datadir):
        self.datadir = datadir
        self.setup_translations()
    
        # Setup config
        self.config = KazamConfig()
    
        # Setup icons
        self.icons = gtk.icon_theme_get_default()
        self.icons.append_search_path(os.path.join(datadir,"icons", "48x48", "apps"))
        self.icons.append_search_path(os.path.join(datadir,"icons", "16x16", "apps"))
        gtk.window_set_default_icon_name("kazam")
        
        # Will be set later, here for convenience
        self.screencast = None
        self.window_countdown = None
        self.indicator = None
        self.done_recording = None
        self.export = None
        
        # Let's start!
        self.recording_start = RecordingStart(self.datadir, self.icons, 
                                                self.config)
        self.recording_start.connect("countdown-requested", self.cb_countdown_requested)
        self.recording_start.connect("quit-requested", gtk.main_quit)
        
    # Functions

    def setup_translations(self):
        gettext.bindtextdomain("kazam", "/usr/share/locale")
        gettext.textdomain("kazam")
        try:
            locale.setlocale(locale.LC_ALL, "")
        except Exception, e:
            logging.exception("setlocale failed")
        
    # Callbacks
        
    def on_window_countdown_count(self, window_countdown):
        self.indicator.count(window_countdown.number)
        
    def cb_record_done_request_requested(self, indicator):
        self.screencast.stop_recording()
        self.done_recording = DoneRecording(self.datadir, self.icons)
        self.done_recording.connect("save-requested", self.cb_save_requested)
        self.done_recording.connect("edit-requested", self.cb_edit_requested)
        self.done_recording.connect("quit-requested", self.cb_quit_requested)
        self.done_recording.run()
        
    def cb_record_requested(self, window_countdown):
        self.indicator.start_recording()
        self.screencast.start_recording()

    def cb_countdown_requested(self, recording_start):
        self.backend = self.recording_start.get_selected_backend()
        if self.backend == "gstreamer":
            from kazam.backend.gstreamer import Screencast
        else:
            from kazam.backend.ffmpeg import Screencast

        self.screencast = Screencast()

        self.audio_source = self.recording_start.checkbutton_audio.get_active()
        self.video_source = self.recording_start.get_selected_video_source()

        self.screencast.setup_sources(self.video_source, self.audio_source)

        self.window_countdown = CountdownWindow(self.datadir, self.icons)
        self.window_countdown.connect("count", self.on_window_countdown_count)
        self.window_countdown.connect("record-requested", self.cb_record_requested)
        self.window_countdown.run()
        
        self.indicator = KazamIndicator(self.config)
        self.indicator.connect("recording-done", self.cb_record_done_request_requested)    
        self.indicator.connect("pause-requested", self.cb_pause_requested)    
        self.indicator.connect("unpause-requested", self.cb_unpause_requested)    
        self.indicator.connect("quit-requested", self.cb_quit_requested)    
        
    def cb_quit_requested(self, indicator):
        self.screencast.stop_recording()
        try:
            os.remove(self.screencast.tempfile)
        except:
            print "Unable to delete temporary file:", self.screencast.tempfile
        gtk.main_quit()

    def cb_pause_requested(self, indicator):
        self.screencast.pause_recording()
        
    def cb_unpause_requested(self, indicator):
        self.screencast.unpause_recording()
    
    def cb_edit_requested(self, done_recording, data):
        (command, args_list) = data
        
        # If the user has selected Kazam, open the export window
        if command.endswith("kazam"):
            self.export = ExportFrontend(self.datadir, self.icons, 
                            self.screencast)
            self.export.connect("back-requested", self.cb_back_done_recording_requested)
            self.export.connect("quit-requested", self.cb_quit_requested)
            self.export.run()
        else:
            args_list.insert(0, command)
            args_list.append(self.screencast.get_recording_filename())
            Popen(args_list)
            gtk.main_quit()
        
    def cb_back_done_recording_requested(self, export):
        del self.done_recording, self.export
        self.cb_record_done_request_requested(None)
        
    def cb_save_requested(self, done_recording):
        # Open the save dialog
        (save_dialog, result) = new_save_dialog(_("Save screencast"), self.backend, 
                                            self.done_recording.window)
        # If the user clicks save
        if result == gtk.RESPONSE_OK:
            # Make sure the filename ends with .mkv
            uri = os.path.join(save_dialog.get_current_folder(), save_dialog.get_filename())
            if self.backend == "ffmpeg":
                if not uri.endswith(".mkv"):
                    uri += ".mkv"
            else:
                if not uri.endswith(".webm"):
                    uri += ".webm"

            # And move the temporary recorded file to the desired save location
            shutil.move(self.screencast.get_recording_filename(), uri)
            # And quit
            gtk.main_quit()
        
    # Functions
    def run(self):
        self.recording_start.run()
        gtk.main()



