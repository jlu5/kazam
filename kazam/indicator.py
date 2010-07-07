#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       indicator.py
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
import gobject
import rsvg

from gettext import gettext as _


try:
    ## Deliberate- indicator not working quite yet
    import appindicator
    class KazamIndicator(appindicator.Indicator, gobject.GObject):
     
        __gsignals__ = {
            "recording-done" : (gobject.SIGNAL_RUN_LAST,
                                       gobject.TYPE_NONE,
                                       (),
                                      ),
        }
        
        def __init__(self, icons):
            self.icons = icons
            
            appindicator.Indicator.__init__(self, "kazam", 
                                "kazam-recording", 
                                appindicator.CATEGORY_APPLICATION_STATUS)
            self.set_attention_icon("kazam-countdown-5")
            self.set_status(appindicator.STATUS_ATTENTION)
          
            self.menu = gtk.Menu()
            self.menuitem_pause = gtk.CheckMenuItem("Pause recording")
            self.menuitem_pause.set_sensitive(False)
            self.menuitem_pause.connect("activate", self.on_menuitem_pause_activate)
            self.menuitem_finish = gtk.MenuItem("Finish recording...")
            self.menuitem_finish.set_sensitive(False)
            self.menuitem_finish.connect("activate", self.on_menuitem_finish_activate)
            self.menuitem_separator = gtk.SeparatorMenuItem()
            self.menuitem_quit = gtk.MenuItem("Quit")
            self.menuitem_quit.connect("activate", self.on_menuitem_quit_activate)
            self.menu.append(self.menuitem_pause)
            self.menu.append(self.menuitem_finish)
            self.menu.append(self.menuitem_separator)
            self.menu.append(self.menuitem_quit)

            self.set_menu(self.menu)
            self.menu.show_all()
        
        def on_menuitem_pause_activate(self, menuitem_pause):
            if menuitem_pause.get_active():
                self.set_icon("kazam-paused")
                print "pause"
            else:
                self.set_icon("kazam-recording")
                print "record"
                
        def on_menuitem_finish_activate(self, menuitem_finish):
            print "finished!"
            self.set_status(appindicator.STATUS_PASSIVE)
            self.emit("recording-done")
            
        def on_menuitem_quit_activate(self, menuitem_quit):
            gtk.main_quit()
        
        def count(self, count):
            self.set_attention_icon("kazam-countdown-%s" % count)
            
        def start_recording(self):
            self.set_icon("kazam-recording")
            self.set_status(appindicator.STATUS_ACTIVE)
            
            #self.menuitem_pause.set_sensitive(True)
            self.menuitem_finish.set_sensitive(True)
            
except ImportError:
    print "Fallback!"
    
    class KazamIndicator(gtk.StatusIcon):
     
        __gsignals__ = {
            "recording-done" : (gobject.SIGNAL_RUN_LAST,
                                       gobject.TYPE_NONE,
                                       (),
                                      ),
        }
        
        def __init__(self, icons):
            gtk.StatusIcon.__init__(self)
            
            self.set_from_icon_name("kazam-countdown-5")
            
            self.menu = gtk.Menu()
            self.menuitem_pause = gtk.CheckMenuItem("Pause recording")
            self.menuitem_pause.set_sensitive(False)
            self.menuitem_pause.connect("activate", self.on_menuitem_pause_activate)
            self.menuitem_finish = gtk.MenuItem("Finish recording...")
            self.menuitem_finish.set_sensitive(False)
            self.menuitem_finish.connect("activate", self.on_menuitem_finish_activate)
            self.menuitem_separator = gtk.SeparatorMenuItem()
            self.menuitem_quit = gtk.MenuItem("Quit")
            self.menuitem_quit.connect("activate", self.on_menuitem_quit_activate)
            self.menu.append(self.menuitem_pause)
            self.menu.append(self.menuitem_finish)
            self.menu.append(self.menuitem_separator)
            self.menu.append(self.menuitem_quit)
            self.menu.show_all()
            self.connect("popup-menu", self.on_status_icon_right_click_event)
            
        def on_status_icon_right_click_event(self, icon, button, time):
            self.menu.popup(None, None, gtk.status_icon_position_menu, button, time, self)
    
        def on_menuitem_pause_activate(self, menuitem_pause):
            if menuitem_pause.get_active():
                self.set_from_icon_name("kazam-paused")
                print "pause"
            else:
                self.set_from_icon_name("kazam-recording")
                print "record"
                
        def on_menuitem_finish_activate(self, menuitem_finish):
            self.set_visible(False)
            self.emit("recording-done")
            
        def on_menuitem_quit_activate(self, menuitem_quit):
            gtk.main_quit()
        
        def count(self, count):
            self.set_from_icon_name("kazam-countdown-%s" % count)
            
        def start_recording(self):
            self.set_from_icon_name("kazam-recording")
            
            #self.menuitem_pause.set_sensitive(True)
            self.menuitem_finish.set_sensitive(True)

