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
import gobject

from SimpleGtkbuilderApp import SimpleGtkbuilderApp
from gettext import gettext as _

from widgets.comboboxes import ExternalEditorCombobox

class DoneRecording(gobject.GObject):
    
    __gsignals__ = {
    "save-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),),
    "edit-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           [gobject.TYPE_PYOBJECT],)
    }

    
    (ACTION_EDIT, ACTION_SAVE) = range(2)
    
    def __init__(self, datadir):
        gobject.GObject.__init__(self)
        
        # Setup UI
        self.builder = gtk.Builder()
        self.builder.add_from_file(os.path.join(datadir, "ui", "done-recording.ui"))
        self.builder.connect_signals(self)
        for o in self.builder.get_objects():
            if issubclass(type(o), gtk.Buildable):
                name = gtk.Buildable.get_name(o)
                setattr(self, name, o)
            else:
                print >> sys.stderr, "WARNING: can not get name for '%s'" % o
        
        self.action = self.ACTION_EDIT
        self.dialog = self.dialog_done_recording
        
        self.dialog.connect("delete-event", gtk.main_quit)
        
        # TODO: Add our file menu
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
        
        self.dialog.vbox.pack_start(self.menubar)
        self.dialog.vbox.reorder_child(self.menubar, 0)
        
        # Add editor combobox
        self.combobox_editors = ExternalEditorCombobox()
        self.table_actions.attach(self.combobox_editors, 1, 2, 0, 1)
        
    def on_button_cancel_clicked(self, button):
        gtk.main_quit()
        
    def on_button_continue_clicked(self, button):
        if self.action == self.ACTION_SAVE:
            self.emit("save-requested")
        elif self.action == self.ACTION_EDIT:
            i = self.combobox_editors.get_active()
            liststore = self.combobox_editors.get_model()
            list_iter = liststore.get_iter(i)
            
            desktop_entry = liststore.get_value(list_iter, 2)
            args = liststore.get_value(list_iter, 3)
            
            self.emit("edit-requested", (desktop_entry, args))
        
    def on_radiobutton_save_as_toggled(self, radiobutton):
        if not radiobutton.get_active():
            return
        else:
            self.action = self.ACTION_SAVE
            self.combobox_editors.set_sensitive(False)
            
    def on_radiobutton_edit_with_toggled(self, radiobutton):
        if not radiobutton.get_active():
            return
        else:
            self.action = self.ACTION_EDIT
            self.combobox_editors.set_sensitive(True)
        
    def run(self):
        response = self.dialog.run()
        self.dialog.hide()
        return response



