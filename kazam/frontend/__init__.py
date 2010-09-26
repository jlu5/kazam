#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       __init__.py
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

import gobject

from kazam.frontend.widgets.dialogs import new_about_dialog

class KazamStage(gobject.GObject):
    
    __gsignals__ = {
    "quit-requested" : (gobject.SIGNAL_RUN_LAST,
                               gobject.TYPE_NONE,
                               (),
                              ),
    }
    
    def __init__(self, datadir, icons):
        super(KazamStage, self).__init__()
        self.datadir = datadir
        self.icons = icons
        
    def on_menuitem_about_activate(self, menuitem):
        new_about_dialog()
        
    def on_menuitem_quit_activate(self, menuitem):
        self.emit("quit-requested")
        
    def on_button_close_clicked(self, button):
        self.emit("quit-requested")
        
    def on_button_cancel_clicked(self, button):
        self.emit("quit-requested")
        
    def run(self):
        self.window.show_all()
