#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       comboboxes.py
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
import glib
import gobject
import os

from xdg.DesktopEntry import DesktopEntry

class EasyComboBox(gtk.ComboBox):
    def __init__(self):
        super(EasyComboBox, self).__init__()
    
    def get_active_value(self, column):
        i = self.get_active()
        liststore = self.get_model()
        list_iter = liststore.get_iter(i)
        return liststore.get_value(list_iter, column)
        
class EasyTextComboBox(EasyComboBox):
    def __init__(self):
        super(EasyTextComboBox, self).__init__()
        
        # Cell renders
        cr_text = gtk.CellRendererText()
        self.pack_start(cr_text, True)
        self.add_attribute(cr_text, 'text', 0)  
        # List store
        liststore = gtk.ListStore(str)
        self.set_model(liststore)

class ExternalEditorCombobox(EasyComboBox):
    
    EDITORS = {
                "/home/andrew/Software/Projects/kazam/data/kazam.desktop.in":[],
                "/usr/share/applications/openshot.desktop":[],
                "/usr/share/applications/pitivi.desktop":["-i", "-a"],
                "/usr/share/applications/avidemux-gtk.desktop":[],
                }
    
    def __init__(self, icons):
        super(ExternalEditorCombobox, self).__init__()
        self.icons = icons 

        # Cell renders
        cr_pixbuf = gtk.CellRendererPixbuf()
        self.pack_start(cr_pixbuf, False)
        self.add_attribute(cr_pixbuf, 'pixbuf', 0)  
        cr_text = gtk.CellRendererText()
        self.pack_start(cr_text, True)
        self.add_attribute(cr_text, 'text', 1)  
        
        # List store
        liststore = gtk.ListStore(gtk.gdk.Pixbuf, str, gobject.TYPE_PYOBJECT, gobject.TYPE_PYOBJECT)
        self.set_model(liststore)
        self._populate()
        
        self.set_active(0)
        self.show()
        
    def _populate(self):
        liststore = self.get_model()
        
        for item in self.EDITORS:
            if os.path.isfile(item):
                args = self.EDITORS[item]
                desktop_entry = DesktopEntry(item)
                name = desktop_entry.getName()
                icon_name = desktop_entry.getIcon()
                try:
                    pixbuf = self.icons.load_icon(icon_name, 16, ())
                except glib.GError:
                    pixbuf = self.icons.load_icon("application-x-executable", 16, ())
            
            liststore.append([pixbuf, name, desktop_entry, args])
            
class ExportCombobox(EasyComboBox):
    
    def __init__(self, icons, export_sources):
        super(ExportCombobox, self).__init__()
        self.icons = icons 

        # Cell renders
        cr_pixbuf = gtk.CellRendererPixbuf()
        self.pack_start(cr_pixbuf, True)
        self.add_attribute(cr_pixbuf, 'pixbuf', 0)  
        cr_text = gtk.CellRendererText()
        self.pack_start(cr_text, True)
        self.add_attribute(cr_text, 'text', 1)  
        
        # List store
        liststore = gtk.ListStore(gtk.gdk.Pixbuf, str, gobject.TYPE_PYOBJECT, str)
        self.set_model(liststore)
        self._populate(export_sources)
        
        self.set_active(0)
        self.show()
        
    def _populate(self, export_sources):
        for source in export_sources:
            name = source
            pixbuf_name = export_sources[name][0]
            pixbuf = self.icons.load_icon(pixbuf_name, 16, ())
            plugin_class = export_sources[name][1]
            plugin_name = export_sources[name][2]
            self.get_model().append([pixbuf, name, plugin_class, plugin_name])
            
class VideoCombobox(EasyComboBox):
    
    SOURCES = ["Screen"]
    
    def __init__(self):
        super(VideoCombobox, self).__init__()

        # Cell renders
        cr_text = gtk.CellRendererText()
        self.pack_start(cr_text, True)
        self.add_attribute(cr_text, 'text', 0)  
        # List store
        liststore = gtk.ListStore(str)
        self.set_model(liststore)
        self._populate()
        
        self.set_active(0)
        self.show()
        
    def _populate(self):
        liststore = self.get_model()
        liststore.append(self.SOURCES)
            
            
class AudioCombobox(EasyComboBox):
    
    SOURCES = ["Computer"]
    
    def __init__(self):
        super(AudioCombobox, self).__init__()

        # Cell renders
        cr_text = gtk.CellRendererText()
        self.pack_start(cr_text, True)
        self.add_attribute(cr_text, 'text', 0)  
        # List store
        liststore = gtk.ListStore(str)
        self.set_model(liststore)
        self._populate()
        
        self.set_active(0)
        self.set_sensitive(False)
        self.show()
        
    def _populate(self):
        liststore = self.get_model()
        liststore.append(self.SOURCES)
            

