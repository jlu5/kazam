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

from widgets.comboboxes import VideoCombobox, AudioCombobox
from utils import *

class RecordingStart(gobject.GObject):
    
    __gsignals__ = {
    "countdown-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),),
    "quit-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),)
    }

    
    def __init__(self, datadir):
        gobject.GObject.__init__(self)
        
        # Setup UI
        setup_ui(self, os.path.join(datadir, "ui", "start.ui"))   
        
        self.dialog = self.dialog_start
        self.dialog.connect("delete-event", gtk.main_quit)
        
        menu_dict = [
                        {
                        "name":"_File",
                        "children":[{
                                "name":"_Quit",
                                "connect":("activate", "on_menuitem_quit_activate")
                                }]
                        },
                        {
                        "name":"_Help",
                        "children":[{
                                "name":"About",
                                "connect":("activate", "on_menuitem_about_activate")
                                }]
                        },
                    ]
        
        # Add our menus
        self.menubar = menubar_from_dict(self, menu_dict)
        
        # Pack them
        self.dialog.vbox.pack_start(self.menubar, False, True)
        self.dialog.vbox.reorder_child(self.menubar, 0)
        
        # Add our comboboxes
        self.combobox_video = VideoCombobox()
        self.combobox_audio = AudioCombobox()
        # Pack them
        self.table_sources.attach(self.combobox_video, 1, 2, 0, 1)
        self.table_sources.attach(self.combobox_audio, 1, 2, 1, 2)
        
    def on_button_close_clicked(self, button):
        gtk.main_quit()
        
    def on_button_record_clicked(self, button):
        self.emit("countdown-requested")
    
    def on_menuitem_quit_activate(self, menuitem):
        self.emit("quit-requested")
        
    def on_menuitem_about_activate(self, menuitem):
        pass
    
    def on_checkbutton_video_toggled(self, checkbutton):
        self.combobox_video.set_sensitive(checkbutton.get_active())
        
    def on_checkbutton_audio_toggled(self, checkbutton):
        self.combobox_audio.set_sensitive(checkbutton.get_active())
        
    def run(self):
        response = self.dialog.run()
        self.dialog.hide()
        return response
        
        

