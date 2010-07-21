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

from xdg.DesktopEntry import DesktopEntry

class ExternalEditorCombobox(gtk.ComboBox):
    
    EDITORS = {
                "/home/andrew/Software/Projects/kazam/data/kazam.desktop.in":[],
                "/usr/share/applications/pitivi.desktop":["-i", "-a"],
                "/usr/share/applications/avidemux-gtk.desktop":[],
                }
    
    def __init__(self, icons):
        gtk.ComboBox.__init__(self)
        self.icons = icons 

        # Cell renders
        cr_pixbuf = gtk.CellRendererPixbuf()
        self.pack_start(cr_pixbuf, True)
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
            args = self.EDITORS[item]
            desktop_entry = DesktopEntry(item)
            name = desktop_entry.getName()
            icon_name = desktop_entry.getIcon()
            try:
                pixbuf = self.icons.load_icon(icon_name, 16, ())
            except glib.GError:
                pixbuf = self.icons.load_icon("application-x-executable", 16, ())
            
            liststore.append([pixbuf, name, desktop_entry, args])
            
class ExportCombobox(gtk.ComboBox):
    
    def __init__(self, icons, export_sources):
        gtk.ComboBox.__init__(self)
        self.icons = icons 

        # Cell renders
        cr_pixbuf = gtk.CellRendererPixbuf()
        self.pack_start(cr_pixbuf, True)
        self.add_attribute(cr_pixbuf, 'pixbuf', 0)  
        cr_text = gtk.CellRendererText()
        self.pack_start(cr_text, True)
        self.add_attribute(cr_text, 'text', 1)  
        
        # List store
        liststore = gtk.ListStore(gtk.gdk.Pixbuf, str, gobject.TYPE_PYOBJECT)
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
            self.get_model().append([pixbuf, name, plugin_class])
            
class VideoCombobox(gtk.ComboBox):
    
    SOURCES = ["Screen"]
    
    def __init__(self):
        gtk.ComboBox.__init__(self)

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
            
            
class AudioCombobox(gtk.ComboBox):
    
    SOURCES = ["Computer"]
    
    def __init__(self):
        gtk.ComboBox.__init__(self)

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
            

