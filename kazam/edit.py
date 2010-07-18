#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       edit.py
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
import gobject

from gettext import gettext as _

from widgets.comboboxes import ExportCombobox
from export_sources.youtube import YouTube
from export_sources.videobin import VideoBin
from export_backend import ExportBackend

from utils import *

class Edit(gobject.GObject):
    
    __gsignals__ = {
    "back-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),),
    "export-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           [gobject.TYPE_PYOBJECT],)
    }
    
    EXPORT_SOURCES = {
                        "YouTube":["gtk-edit", YouTube],
                        "VideoBin":["gtk-edit", VideoBin]
                    }
    
    def __init__(self, datadir, icons):
        super(Edit, self).__init__()
        self.icons = icons
        self.backend = ExportBackend(self)
        self.backend.connect("export-completed", self.cb_export_completed)
        self.previous_source = None
        
        # Setup UI
        setup_ui(self, os.path.join(datadir, "ui", "edit.ui"))        
        
        self.window = self.window_edit
        
        self.window_edit.connect("delete-event", gtk.main_quit)
        
        # Add export combobox
        self.combobox_export = ExportCombobox(self.icons, self.EXPORT_SOURCES)
        self.combobox_export.connect("changed", self.on_combobox_export_changed)
        self.hbox_export.pack_start(self.combobox_export, False, True)
        
        # Add our export properties
        self.on_combobox_export_changed(None)
        
    def on_button_close_clicked(self, button):
        gtk.main_quit()
        
    def on_button_back_clicked(self, button):
        self.emit("back-requested")
        
    def on_button_export_clicked(self, button):
        export_class = get_combobox_active_value(self.combobox_export, 2)
        self.emit("export-requested", export_class)
        
        getattr(self, "alignment_%s" % self.previous_source.lower()).set_sensitive(False)
        self.button_export.set_sensitive(False)
        self.button_back.set_sensitive(False)
        self.combobox_export.set_sensitive(False)
        
    def on_combobox_export_changed(self, combobox):
        if self.previous_source:
             self.vbox_main.remove(getattr(self, "alignment_%s" % self.previous_source.lower()))
        name = get_combobox_active_value(self.combobox_export, 1)
        alignment = getattr(self, "alignment_%s" % name.lower())
        self.vbox_main.pack_start(alignment, True, True)
        self.vbox_main.reorder_child(alignment, 3)
        
        self.previous_source = name
        
    def on_menuitem_quit_activate(self, button):
        gtk.main_quit()
        
    def on_menuitem_about_activate(self, button):
        pass
        
    def get_meta(self):
        source_class = get_combobox_active_value(self.combobox_export, 2)
        meta = source_class.META.copy()
        for key in source_class.META:
            var_name = source_class.META[key][0]
            func_name = source_class.META[key][1]
            var = getattr(self, var_name)
            source_class.META[key] = getattr(var, func_name)()
        return meta
    
    def get_property_value(self, widget):
        if isinstance(widget, gtk.TextEntry):
            return widget.get_text()
        elif isinstance(widget, gtk.TextView):
            return widget.get_buffer().get_text()
        elif isinstance(widget, gtk.ComboBox):
            return get_combobox_active_value(widget, 1)
    
    def cb_export_completed(self, url):
        print url
        
    def run(self):
        self.window_edit.show_all()

if __name__ == "__main__":
    icons = gtk.icon_theme_get_default()
    
    if os.path.exists("./data/ui/edit.ui"):
        logging.info("Running locally")
        datadir = "./data"
    else:
        datadir = "/usr/share/kazam/"
    
    done_recording = Edit(datadir, icons)
    #done_recording.connect("save-requested", gtk.main_quit)
    #done_recording.connect("edit-requested", gtk.main_quit)
    done_recording.run()
    gtk.main()


