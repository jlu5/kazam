#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       window_start.py
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

import gtk
import gobject
import os

from gettext import gettext as _

from kazam.frontend import KazamStage
from kazam.frontend.widgets.comboboxes import VideoCombobox, AudioCombobox, BackendCombobox
from kazam.utils import *

class RecordingStart(KazamStage):
    
    __gsignals__ = {
    "countdown-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),),
    }

    
    def __init__(self, datadir, icons, config, audio_sources):
        super(RecordingStart, self).__init__(datadir, icons)
        self.config = config

        self.audio_sources = audio_sources
        
        # Setup UI
        setup_ui(self, os.path.join(datadir, "ui", "start.ui"))   
        
        self.window = self.window_start
        self.window.connect("delete-event", gtk.main_quit)
        
        # Add our comboboxes
        self.combobox_video = VideoCombobox()
        self.combobox_audio = AudioCombobox(self.audio_sources)
        self.combobox_backend = BackendCombobox()
        # Pack them
        self.table_sources.attach(self.combobox_video, 1, 2, 0, 1)
        self.table_sources.attach(self.combobox_audio, 1, 2, 1, 2)
        self.table_sources.attach(self.combobox_backend, 1, 2, 2, 3)
        
        # Make widgets as they were the last time they were used
        self.restore_last_state()
        
    # Functions
        
    def restore_last_state(self):
        video_toggled = self.config.getboolean("start_recording", "video_toggled")
        self.checkbutton_video.set_active(video_toggled)
        audio_toggled = self.config.getboolean("start_recording", "audio_toggled")
        self.checkbutton_audio.set_active(audio_toggled)
        
        video_source = self.config.getint("start_recording", "video_source")
        self.combobox_video.set_active(video_source)
        audio_source = self.config.getint("start_recording", "audio_source")
        self.combobox_audio.set_active(audio_source)
        backend = self.config.getint("start_recording", "backend")
        self.combobox_backend.set_active(backend)

        # Make sure sensitivity of comboboxes is updated
        self.on_checkbutton_video_toggled(self.checkbutton_video)
        self.on_checkbutton_audio_toggled(self.checkbutton_audio)
        
    def save_last_state(self):
        video_toggled = self.checkbutton_video.get_active()
        self.config.set("start_recording", "video_toggled", video_toggled)
        audio_toggled = self.checkbutton_audio.get_active()
        self.config.set("start_recording", "audio_toggled", audio_toggled)
        
        video_source = self.combobox_video.get_active()
        self.config.set("start_recording", "video_source", video_source)
        audio_source = self.combobox_audio.get_active()
        self.config.set("start_recording", "audio_source", audio_source)
        backend = self.combobox_backend.get_active()
        self.config.set("start_recording", "backend", backend)
        self.config.write()
        
    # Callbacks
        
    def on_button_close_clicked(self, button):
        self.save_last_state()
        super(RecordingStart, self).on_button_close_clicked(button)
        
    def on_button_record_clicked(self, button):
        self.emit("countdown-requested")
        self.save_last_state()
        self.window.destroy()
    
    def on_menuitem_quit_activate(self, menuitem):
        self.save_last_state()
        super(RecordingStart, self).on_menuitem_quit_activate(menuitem)
    
    def on_checkbutton_video_toggled(self, checkbutton):
        self.combobox_video.set_sensitive(checkbutton.get_active())
        self.sensitise_record_button()

    def on_checkbutton_audio_toggled(self, checkbutton):
        self.combobox_audio.set_sensitive(checkbutton.get_active())
        self.sensitise_record_button()

    def sensitise_record_button(self):
        video_source = self.checkbutton_video.get_active()
        audio_source = self.checkbutton_audio.get_active()
        self.button_record.set_sensitive(video_source or audio_source)
        
    def get_selected_video_source(self):
        if not self.checkbutton_video.get_active():
            return None
        return self.combobox_video.get_selected_video_source()
        
    def get_selected_audio_source(self):
        if not self.checkbutton_audio.get_active():
            return None
        return self.combobox_audio.get_selected_audio_source()
        
    def get_selected_backend(self):
        return self.combobox_backend.get_selected_backend()


