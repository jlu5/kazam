# -*- coding: utf-8 -*-
#
#       window_countdown.py
#
#       Copyright 2012 David Klasinc <bigwhale@lubica.net>
#       Copyright 2010 Andrew <andrew@karmic-desktop>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
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

import logging
import cairo
import os
import time

from gettext import gettext as _

from gi.repository import Gtk, GObject

class CountdownWindow(GObject.GObject):

    __gsignals__ = {
        "start-request" : (GObject.SIGNAL_RUN_LAST,
                                   None,
                                   (),
                                  ),
    }

    def __init__(self, number = 5):
        super(CountdownWindow, self).__init__()
        self.window = Gtk.Window()
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_border_width(30)
        self.window.set_app_paintable(True)
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("draw", self.cb_draw)

        self.number = number
        box = Gtk.VBox()
        self.lbl_text = Gtk.Label()
        rec_markup = _("<span size='35000' foreground='#FFFFFF'>Recording will start in ...</span>")
        self.lbl_text.set_markup(rec_markup)
        self.lbl_number = Gtk.Label()
        num_markup = _("<span size='40000' foreground='#FFFFFF'>%d</span>" % self.number)
        self.lbl_number.set_markup(num_markup)
        box.add(self.lbl_text)
        box.add(self.lbl_number)
        self.window.add(box)

        self.window.set_decorated(False)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_keep_above(True)
        self.screen = self.window.get_screen()
        self.visual = self.screen.get_rgba_visual()

        if self.visual != None and self.screen.is_composited():
            self.window.set_visual(self.visual)


    def run(self, counter):
        self.number = counter
        self.window.show_all()
        self.countdown()

    def countdown(self):
        if self.number != 0:
            num_markup = _("<span size='40000' foreground='#FFFFFF'>%d</span>" % self.number)
            self.lbl_number.set_markup(num_markup)
            self.window.queue_draw()
            GObject.timeout_add(1000, self.countdown)
            self.number -= 1
        else:
            self.emit("start-request")
            self.window.destroy()

    def cb_draw(self, widget, cr):
        w = widget.get_preferred_width()[0]
        h = widget.get_preferred_height()[0]
        cr.set_source_rgba(1, 1, 1, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        self.draw_rounded(cr, 1, 1, w-10, h-10, 20)
        cr.set_line_width(1.0)
        cr.set_source_rgba(.2, .2, .2, 0.8)
        cr.stroke_preserve()
        cr.fill()
        cr.set_operator(cairo.OPERATOR_OVER)

    def draw_rounded(self, cr, x, y, w, h, r=20):
        cr.move_to(x+r,y)
        cr.line_to(x+w-r,y)
        cr.curve_to(x+w,y,x+w,y,x+w,y+r)
        cr.line_to(x+w,y+h-r)
        cr.curve_to(x+w,y+h,x+w,y+h,x+w-r,y+h)
        cr.line_to(x+r,y+h)
        cr.curve_to(x,y+h,x,y+h,x,y+h-r)
        cr.line_to(x,y+r)
        cr.curve_to(x,y,x,y,x+r,y)

