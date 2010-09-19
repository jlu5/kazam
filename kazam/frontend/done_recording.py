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

from gettext import gettext as _

from kazam.frontend.widgets.comboboxes import ExternalEditorCombobox
from kazam.frontend.widgets.dialogs import new_about_dialog
from kazam.utils import *

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
    
    def __init__(self, datadir, icons):
        gobject.GObject.__init__(self)
        self.icons = icons
        
        # Setup UI
        setup_ui(self, os.path.join(datadir, "ui", "done-recording.ui"))        
                
        self.action = self.ACTION_EDIT
        self.window = self.window_done_recording
        self.window.connect("delete-event", gtk.main_quit)
        
        # Add editor combobox
        self.combobox_editors = ExternalEditorCombobox(self.icons)
        self.table_actions.attach(self.combobox_editors, 1, 2, 0, 1, gtk.FILL, gtk.FILL)
        
    def on_button_cancel_clicked(self, button):
        gtk.main_quit()
        
    def on_menuitem_quit_activate(self, button):
        gtk.main_quit()
        
    def on_menuitem_about_activate(self, menuitem):
        new_about_dialog()
        
    def on_button_continue_clicked(self, button):
        if self.action == self.ACTION_SAVE:
            self.emit("save-requested")
            self.window.destroy()
        elif self.action == self.ACTION_EDIT:
            command = self.combobox_editors.get_active_value(2)
            args = self.combobox_editors.get_active_value(3)
            self.window.destroy()
            self.emit("edit-requested", (command, args))
        
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
        self.window.show_all()

if __name__ == "__main__":
    icons = gtk.icon_theme_get_default()
    
    if os.path.exists("./data/ui/start.ui"):
        logging.info("Running locally")
        datadir = "./data"
    else:
        datadir = "/usr/share/kazam/"
    
    done_recording = DoneRecording(datadir, icons)
    done_recording.connect("save-requested", gtk.main_quit)
    done_recording.connect("edit-requested", gtk.main_quit)
    done_recording.run()
    gtk.main()


