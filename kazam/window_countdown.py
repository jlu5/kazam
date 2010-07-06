#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       window_countdown.py
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
import cairo
import gtk.gdk as gdk
import gobject
import rsvg
import gobject

from gettext import gettext as _

class CountdownWindow(gtk.Window):
 
    __gsignals__ = {
        "done" : (gobject.SIGNAL_RUN_LAST,
                                   gobject.TYPE_NONE,
                                   (),
                                  ),
        "count" : (gobject.SIGNAL_RUN_LAST,
                                   gobject.TYPE_NONE,
                                   (),
                                  ),
    }
 
    def __init__(self):
        
        self.number = 5
        self.svg = rsvg.Handle(file="../data/ui/countdown.svg")
        
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(420, 220)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_app_paintable(True)
        # Window events
        self.connect("expose-event", self.on_window_countdown_expose_event)
        self.connect("screen-changed", self.screen_changed_cb)
        # Add button press event
        self.add_events(gdk.BUTTON_PRESS_MASK)
        self.connect ("button_press_event", self.button_press_cb)
        # Do not show the window decoration
        self.set_decorated (False)
        self.set_property("skip-taskbar-hint", True)
        self.screen_changed_cb(self, None)
        self.show_all()
        gobject.timeout_add(1000, self.countdown)
        
 
    def on_window_countdown_expose_event(self, widget, event_expose):
        # Create cairo surface
        cairo_context = widget.window.cairo_create()
        cairo_context.set_source_rgba (1.0, 1.0, 1.0, 0.0)
        cairo_context.set_operator(cairo.OPERATOR_SOURCE)
        cairo_context.paint()
        # Render our SVG onto it
        self.svg.render_cairo(cairo_context)
        # Write our text
        cairo_context.set_source_rgba(1, 1, 1, 1.0)
        cairo_context.move_to(65, 70)
        cairo_context.select_font_face("Aller", cairo.FONT_SLANT_NORMAL, 
                                        cairo.FONT_WEIGHT_NORMAL)
        cairo_context.set_font_size(28)
        cairo_context.show_text("Recording will start in...")
        cairo_context.move_to(200, 150)
        cairo_context.set_font_size(56)
        cairo_context.show_text(str(self.number))
        return True
 
    def screen_changed_cb(self, widget, previous_screen):
        # Set transparency if possible
        screen = widget.get_screen()
        colormap = screen.get_rgba_colormap()
        if colormap is None:
            colormap = screen.get_rgb_colormap()
        widget.set_colormap(colormap)
 
    def button_press_cb(self, button, button_event):
        # Move the window
        if button_event.button is 1:
            self.begin_move_drag(int(button_event.button), int(button_event.x_root), int(button_event.y_root), button_event.time) 
        return False
        
    def countdown(self):
        if self.number != 1:
            self.number -= 1
            self.emit("count")
            self.queue_draw()
            gobject.timeout_add(1000, self.countdown)
        else:
            self.emit("done")
            self.destroy()



