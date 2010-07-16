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
                "/usr/share/applications/pitivi.desktop":["-i", "-a"]
                }
    
    def __init__(self):
        gtk.ComboBox.__init__(self)


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
        icon_theme = gtk.icon_theme_get_default()
        
        for item in self.EDITORS:
            args = self.EDITORS[item]
            desktop_entry = DesktopEntry(item)
            name = desktop_entry.getName()
            icon_name = desktop_entry.getIcon()
            try:
                pixbuf = icon_theme.load_icon(icon_name, 16, ())
            except glib.GError:
                pixbuf = icon_theme.load_icon("application-x-executable", 16, ())
            
            liststore.append([pixbuf, name, desktop_entry, args])
            
            
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

