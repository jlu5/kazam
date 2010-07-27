#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       export_frontend.py
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

from widgets.comboboxes import ExportCombobox, EasyComboBox
from export_backend import ExportBackend
from utils import *

from export_sources.youtube import *
from export_sources.videobin import *

class ExportFrontend(gobject.GObject):
    
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
    
    def __init__(self, datadir, icons, path):
        super(ExportFrontend, self).__init__()
        self.icons = icons
        self.path = path
        self.backend = ExportBackend(self)
        self.backend.connect("login-started", self.cb_login_started)
        self.backend.connect("login-completed", self.cb_login_completed)
        self.backend.connect("upload-started", self.cb_upload_started)
        self.backend.connect("upload-completed", self.cb_upload_completed)
        self.properties_alignment = None
        
        # Setup UI
        setup_ui(self, os.path.join(datadir, "ui", "edit.ui"))        
        
        # Get window
        self.window = self.window_edit
        self.window_edit.connect("delete-event", gtk.main_quit)
        
        # Add and setup export combobox
        self.combobox_export = ExportCombobox(self.icons, self.EXPORT_SOURCES)
        self.combobox_export.connect("changed", self.on_combobox_export_changed)
        self.hbox_export.pack_start(self.combobox_export, False, True)
        self.hbox_export.reorder_child(self.combobox_export, 1)
        self.on_combobox_export_changed(None)
        
    def on_button_close_clicked(self, button):
        gtk.main_quit()
        
    def on_button_back_clicked(self, button):
        self.emit("back-requested")
        
    def on_button_export_clicked(self, button):
        # Get the export class from combobox
        export_class = self.combobox_export.get_active_value(2)
        self.emit("export-requested", export_class)
        
    def on_combobox_export_changed(self, combobox):
        # If we already have an alignment, unpack it
        if self.properties_alignment:
             self.vbox_main.remove(self.properties_alignment)
        # Get name from combobox...
        name = self.combobox_export.get_active_value(1)
        # .. and correspond it to a property alignment
        self.properties_alignment = getattr(self, "alignment_%s" % name.lower())
        
        # Run an extra GUI function that is defined by uploadsource
        export_class = self.combobox_export.get_active_value(2)
        func_name = "%s_extra_gui" % name
        globals()[func_name](self, export_class, self.properties_alignment)
        
        # Pack our alignment
        self.vbox_main.pack_start(self.properties_alignment, True, True)
        self.vbox_main.reorder_child(self.properties_alignment, 3)
        
    def on_menuitem_quit_activate(self, button):
        gtk.main_quit()
        
    def on_menuitem_about_activate(self, button):
        pass
        
    def _change_status(self, img, text):
        for child in self.hbox_status.get_children():
            child.destroy()
        if img == "spinner":
            img_widget = gtk.Spinner()
            img_widget.start()
        else:
            img_widget = gtk.image_new_from_stock(img, gtk.ICON_SIZE_MENU)
        text_widget = gtk.Label(text)
        self.hbox_status.pack_start(img_widget, False, False)
        self.hbox_status.pack_start(text_widget, False, False)
        self.hbox_status.show_all()
        
    def get_path(self):
        return self.path
        
    def get_meta(self):
        # Get source class from combobox
        source_class = self.combobox_export.get_active_value(2)
        # Copy our meta dict from source class
        meta = source_class.META.copy()
        # For every property in the meta dict...
        for prop in meta:
            # ..get the corresponding widget in the meta dict
            widget = getattr(self, meta[prop])
            # ...get the corresponding widget value and add to the dict
            # inplace of the widget
            meta[prop] = self.get_property_value(widget)
        return meta
    
    def get_property_value(self, widget):
        # Convenience function to get property value based on widget type
        if isinstance(widget, gtk.Entry):
            return widget.get_text()
        elif isinstance(widget, gtk.TextView):
            buf = widget.get_buffer()
            return buf.get_text(buf.get_start_iter(), buf.get_end_iter())
        elif issubclass(widget.__class__, EasyComboBox):
            return widget.get_active_value(0)
    
    def cb_login_started(self, backend):
        self._change_status("spinner", "Logging in...")
        
        # Set buttons, combobox and the alignment insensitive
        # TODO: make this better
        self.properties_alignment.set_sensitive(False)
        self.button_export.set_sensitive(False)
        self.button_back.set_sensitive(False)
        self.combobox_export.set_sensitive(False)
        
    def cb_login_completed(self, backend, success):
        if success:
            self._change_status(gtk.STOCK_OK, "Log-in completed.")
        else:
            self._change_status(gtk.STOCK_DIALOG_ERROR, "There was an error logging in.")
            # Set buttons, combobox and the alignment sensitive
            # TODO: make this better
            self.properties_alignment.set_sensitive(True)
            self.button_export.set_sensitive(True)
            self.button_back.set_sensitive(True)
            self.combobox_export.set_sensitive(True)
            
    def cb_upload_started(self, backend):
        self._change_status("spinner", "Uploading screencast...")
        
    def cb_upload_completed(self, backend, success, url):
        if success:
            self._change_status(gtk.STOCK_OK, "Screencast uploaded.")
            print url
        else:
            self._change_status(gtk.STOCK_DIALOG_ERROR, "There was an error uploading.")
        
    def run(self):
        self.window_edit.show_all()

if __name__ == "__main__":
    icons = gtk.icon_theme_get_default()
    
    if os.path.exists("./data/ui/edit.ui"):
        logging.info("Running locally")
        datadir = "./data"
    else:
        datadir = "/usr/share/kazam/"
    
    done_recording = ExportFrontend(datadir, icons, path)
    #done_recording.connect("save-requested", gtk.main_quit)
    #done_recording.connect("edit-requested", gtk.main_quit)
    done_recording.run()
    gtk.main()


