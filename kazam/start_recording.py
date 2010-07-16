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

class RecordingStart(gobject.GObject):
    
    __gsignals__ = {
    "countdown-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),)
    }

    
    def __init__(self, datadir):
        gobject.GObject.__init__(self)
        
        # Setup UI
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(datadir, "ui", "start.ui"))
        self.builder.connect_signals(self)
        for o in self.builder.get_objects():
            if issubclass(type(o), gtk.Buildable):
                name = gtk.Buildable.get_name(o)
                setattr(self, name, o)
            else:
                print >> sys.stderr, "WARNING: can not get name for '%s'" % o
        
        self.dialog = self.dialog_start
        self.dialog.connect("delete-event", gtk.main_quit)
        
        # Add our menus
        self.menubar = gtk.MenuBar()
        self.file_menuitem = gtk.MenuItem("_File", True)
        self.file_menu = gtk.Menu()
        self.file_menuitem.set_submenu(self.file_menu)
        self.quit_menuitem = gtk.MenuItem("Quit", True)
        self.help_menuitem = gtk.MenuItem("_Help", True)
        self.help_menu = gtk.Menu()
        self.help_menuitem.set_submenu(self.help_menu)
        self.about_menuitem = gtk.MenuItem("About", True)
        self.menubar.append(self.file_menuitem)
        self.menubar.append(self.help_menuitem)
        self.file_menu.append(self.quit_menuitem)
        self.help_menu.append(self.about_menuitem)
        self.menubar.show_all()
        # Pack them
        self.dialog.vbox.pack_start(self.menubar)
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
        gtk.main_quit()
    
    def on_checkbutton_video_toggled(self, checkbutton):
        self.combobox_video.set_sensitive(checkbutton.get_active())
        
    def on_checkbutton_audio_toggled(self, checkbutton):
        self.combobox_audio.set_sensitive(checkbutton.get_active())
        
    def run(self):
        response = self.dialog.run()
        self.dialog.hide()
        return response
        
        
        
        
        
        
        
        
        
        
        
        

