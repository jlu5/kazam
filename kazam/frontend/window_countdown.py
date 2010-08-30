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
import os

from gettext import gettext as _

class CountdownWindow(gtk.Window):
 
    __gsignals__ = {
        "record-requested" : (gobject.SIGNAL_RUN_LAST,
                                   gobject.TYPE_NONE,
                                   (),
                                  ),
        "count" : (gobject.SIGNAL_RUN_LAST,
                                   gobject.TYPE_NONE,
                                   (),
                                  ),
    }
 
    def __init__(self, datadir):
        self.number = 5
        self.svg = rsvg.Handle(file=os.path.join(datadir, 
                                                "images", 
                                                "countdown.svg"))
        
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_default_size(420, 220)
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_app_paintable(True)
        # Window events
        self.connect("expose-event", self.on_window_countdown_expose_event)
        self.connect("screen-changed", self.on_window_screen_changed)
        # Add button press event
        self.add_events(gdk.BUTTON_PRESS_MASK)
        self.connect("button_press_event", self.on_window_button_press_event)
        # Do not show the window decoration
        self.set_decorated (False)
        self.set_property("skip-taskbar-hint", True)
        self.on_window_screen_changed(self, None)
        self.set_keep_above(True)

    def _print_text_center_aligned(self, cairo_context, text, y_pos):
        x1, y1, x2, y2 = cairo_context.clip_extents()
        center_x = (x2 - x1) / 2.0
        x_bearing, y_bearing, tw, th = cairo_context.text_extents(text)[:4]
                
        hw = tw / 2.0
        cairo_context.move_to(center_x - hw - x_bearing, y_pos)
        cairo_context.show_text(text)
        
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
        cairo_context.select_font_face("Aller", cairo.FONT_SLANT_NORMAL, 
                                        cairo.FONT_WEIGHT_NORMAL)

        #Set the font size before rendering center aligned
        cairo_context.set_font_size(28)                                        
        self._print_text_center_aligned(cairo_context, "Recording will start in...", 70)

        cairo_context.set_font_size(56)
        self._print_text_center_aligned(cairo_context, str(self.number), 150)
                         
        return True
 
    def on_window_screen_changed(self, widget, previous_screen):
        # Set transparency if possible
        screen = widget.get_screen()
        colormap = screen.get_rgba_colormap()
        if colormap is None:
            colormap = screen.get_rgb_colormap()
        widget.set_colormap(colormap)
 
    def on_window_button_press_event(self, button, button_event):
        # Move the window
        if button_event.button is 1:
            self.begin_move_drag(int(button_event.button), int(button_event.x_root), int(button_event.y_root), button_event.time) 
        return False
        
    def run_countdown(self):
        self.show_all()
        gobject.timeout_add(1000, self.countdown)
        
    def countdown(self):
        if self.number != 1:
            self.number -= 1
            self.emit("count")
            self.queue_draw()
            gobject.timeout_add(1000, self.countdown)
        else:
            self.emit("record-requested")
            self.destroy()



