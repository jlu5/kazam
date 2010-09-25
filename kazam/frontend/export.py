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

from kazam.frontend.widgets.comboboxes import ExportCombobox, \
    EasyComboBox, EasyTextAndObjectComboBox
from kazam.frontend.widgets.dialogs import *
from kazam.backend.export import ExportBackend
from kazam.utils import *

class ExportFrontend(gobject.GObject):
    
    __gsignals__ = {
    "back-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),),
    "export-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),)
    }
    
    def __init__(self, datadir, icons, screencast):
        super(ExportFrontend, self).__init__()
        self.icons = icons
        self.screencast = screencast
        self.datadir = datadir
        self.backend = ExportBackend(self, datadir)
        self.backend.connect("authenticate-requested", self.cb_authenticate_requested)
        self.backend.connect("login-started", self.cb_login_started)
        self.backend.connect("login-completed", self.cb_login_completed)
        self.backend.connect("convert-started", self.cb_convert_started)
        self.backend.connect("convert-completed", self.cb_convert_completed)
        self.backend.connect("upload-started", self.cb_upload_started)
        self.backend.connect("upload-completed", self.cb_upload_completed)
        
        self.active_alignment = None
        
        # Setup UI
        setup_ui(self, os.path.join(datadir, "ui", "export.ui"))     
        
        # Get window
        self.window = self.window_export
        self.window.connect("delete-event", gtk.main_quit)
        
        # Quality Slider Stuff
        self.adjustment_quality_video = gtk.Adjustment(3000, 200, 6001, 1)
        self.hscale_quality_video = gtk.HScale(self.adjustment_quality_video)
        self.hscale_quality_video.set_draw_value(False)
        self.hbox_quality_video.pack_start(self.hscale_quality_video)
        self.adjustment_quality_audio = gtk.Adjustment(112, 32, 256, 1)
        self.hscale_quality_audio = gtk.HScale(self.adjustment_quality_audio)
        self.hscale_quality_audio.set_draw_value(False)
        self.hbox_quality_audio.pack_start(self.hscale_quality_audio)
        
        # Export combobox stuff
        export_objects = self.backend.get_export_objects()
        export_object_details = []
        for obj in export_objects:
            name = obj.NAME
            icon = obj.ICONS[0]
            tup = (icon, name)
            export_object_details.append(tup)
        
        self.combobox_export = ExportCombobox(self.icons, export_object_details)
        self.combobox_export.connect("changed", self.on_combobox_export_changed)
        self.hbox_export.pack_start(self.combobox_export, False, True)
        self.hbox_export.reorder_child(self.combobox_export, 1)
        self.on_combobox_export_changed(None)
        
    def on_button_close_clicked(self, button):
        gtk.main_quit()
        
    def on_button_back_clicked(self, button):
        self.emit("back-requested")
        self.window.destroy()
        
    def on_button_export_clicked(self, button):
        self.emit("export-requested")
        
    def on_combobox_export_changed(self, combobox):
        # If we already have an alignment, unpack it
        if self.active_alignment:
             self.vbox_main.remove(self.active_alignment)
        
        # Get our current item's object
        i = self.combobox_export.get_active()
        active_object = self.backend.set_active_export_object(i)
        # And its alignment
        self.active_alignment = active_object.alignment_properties
        
        # Run the alignment's expose function
        active_object.property_alignment_expose()
        
        # Pack our alignment
        self.vbox_main.pack_start(self.active_alignment, True, True)
        self.vbox_main.reorder_child(self.active_alignment, 2)
        
    def on_menuitem_quit_activate(self, button):
        gtk.main_quit()
        
    def on_menuitem_about_activate(self, menuitem):
        new_about_dialog()
        
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
        
    def get_screencast(self):
        return self.screencast
        
    def get_meta(self):
        active_export_object = self.backend.get_active_export_object()
        meta = active_export_object.META.copy()
        # For every property in the meta dict...
        for prop in meta:
            # ..get the corresponding widget in the meta dict
            widget = getattr(active_export_object, meta[prop])
            # ...get the corresponding widget value and add to the dict
            # inplace of the widget
            meta[prop] = self.get_property_value(widget)
        return meta
    
    def get_video_quality(self):
        return self.adjustment_quality_video.get_value()
    
    def get_audio_quality(self):
        return self.adjustment_quality_audio.get_value()
    
    def get_property_value(self, widget):
        # Convenience function to get property value based on widget type
        if isinstance(widget, gtk.Entry):
            return widget.get_text()
        elif isinstance(widget, gtk.TextView):
            buf = widget.get_buffer()
            return buf.get_text(buf.get_start_iter(), buf.get_end_iter())
        elif isinstance(widget, EasyTextAndObjectComboBox):
            tuple_ = (widget.get_active_value(0), widget.get_active_value(1))
            return tuple_
        elif issubclass(widget.__class__, EasyComboBox):
            return widget.get_active_value(0)
    
    def sensitise_content_action_widgets(self, sensitive):
        self.active_alignment.set_sensitive(sensitive)
        self.button_export.set_sensitive(sensitive)
        self.button_back.set_sensitive(sensitive)
        self.combobox_export.set_sensitive(sensitive)
        self.label_export.set_sensitive(sensitive)
    
    def cb_authenticate_requested(self, backend, icons, name, register_url):
        authenticate_dialog = AuthenticateDialog(self.datadir, name, self.icons, icons, register_url)
        authenticate_dialog.window.set_transient_for(self.window)
        authenticate_dialog.run()
        self.window.set_sensitive(False)
        while (not hasattr(authenticate_dialog, "details")):
            if authenticate_dialog.action == authenticate_dialog.ACTION_CANCEL:
                break
            gtk.main_iteration()
        self.window.set_sensitive(True)
        if authenticate_dialog.action == authenticate_dialog.ACTION_CANCEL:
            return
        self.backend.details = authenticate_dialog.details
        
    def cb_login_started(self, backend):
        self._change_status("spinner", _("Logging in..."))
        
        # Set buttons, combobox and the alignment insensitive
        self.sensitise_content_action_widgets(False)

        
    def cb_login_completed(self, backend, success):
        if success:
            self._change_status(gtk.STOCK_OK, _("Log-in completed."))
        else:
            self._change_status(gtk.STOCK_DIALOG_ERROR, _("There was an error logging in."))
            # Set buttons, combobox and the alignment sensitive
            self.sensitise_content_action_widgets(True)
            
    def cb_convert_started(self, backend):
        self._change_status("spinner", _("Converting screencast..."))
        
    def cb_convert_completed(self, backend, success):
        if success:
            self._change_status(gtk.STOCK_OK, _("Screencast converted."))
        else:
            self._change_status(gtk.STOCK_DIALOG_ERROR, _("There was an error converting."))
            # Set buttons, combobox and the alignment sensitive
            self.sensitise_content_action_widgets(True)
            
    def cb_upload_started(self, backend):
        self._change_status("spinner", _("Uploading screencast..."))
        
    def cb_upload_completed(self, backend, success, url):
        if success:
            self._change_status(gtk.STOCK_OK, _("Screencast uploaded."))
            # Set buttons, combobox and the alignment sensitive
            self.sensitise_content_action_widgets(True)
            # Show a dialog with the url of the uploaded file
            new_linkbutton_dialog(url, _("Your screencast has uploaded successfully."),
                            _("It is available at the location below:"), self.window)
        else:
            self._change_status(gtk.STOCK_DIALOG_ERROR, _("There was an error uploading."))
            # Set buttons, combobox and the alignment sensitive
            self.sensitise_content_action_widgets(True)
        
    def run(self):
        self.window_export.show_all()

if __name__ == "__main__": 
    if os.path.exists("./data/ui/export.ui"):
        logging.info("Running locally")
        datadir = "./data"
    else:
        datadir = "/usr/share/kazam/"
    icons = gtk.icon_theme_get_default()
    icons.append_search_path(os.path.join(datadir,"icons", "48x48", "apps"))
    icons.append_search_path(os.path.join(datadir,"icons", "16x16", "apps"))
    
    done_recording = ExportFrontend(datadir, icons, "/tmp/hi.mkv")
    #done_recording.connect("save-requested", gtk.main_quit)
    #done_recording.connect("edit-requested", gtk.main_quit)
    done_recording.run()
    gtk.main()


