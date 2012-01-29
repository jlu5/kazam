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

import cairo

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
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("draw", self.cb_draw)
        self.width = 600
        self.height = 240
        self.window.set_default_geometry(self.height, self.width)
        self.window.set_default_size(self.width, self.height)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_app_paintable(True)
        self.window.set_has_resize_grip(False)
        self.window.set_resizable(True)
        self.number = number

        self.window.set_decorated(False)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_keep_above(True)
        self.screen = self.window.get_screen()
        self.visual = self.screen.get_rgba_visual()

        if self.visual is not None and self.screen.is_composited():
            self.window.set_visual(self.visual)


    def run(self, counter):
        self.number = counter + 1
        self.window.show_all()
        self.countdown()

    def countdown(self):
        if self.number > 1:
            self.window.queue_draw()
            GObject.timeout_add(1000, self.countdown)
            self.number -= 1
        else:
            self.window.destroy()
            GObject.timeout_add(400, self.start_request)

    def start_request(self):
        self.emit("start-request")
        return False

    def cb_draw(self, widget, cr):
        w = self.width
        h = self.height
        cr.set_source_rgba(1, 1, 1, 0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        self._draw_rounded(cr, 1, 1, w - 10, h - 10, 20)
        cr.set_line_width(1.0)
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.4)
        cr.stroke_preserve()
        cr.fill()
        cr.set_operator(cairo.OPERATOR_OVER)
        self._outline_text(cr, w, h, 36, _("Recording will start in ..."))
        self._outline_text(cr, w, h + 70, 36, _("{0}".format(self.number)))

    def _draw_rounded(self, cr, x, y, w, h, r = 20):
        cr.move_to(x + r, y)
        cr.line_to(x + w - r, y)
        cr.curve_to(x + w,y,x+w,y,x+w,y+r)
        cr.line_to(x + w,y+h-r)
        cr.curve_to(x + w, y + h, x + w, y + h, x + w - r, y + h)
        cr.line_to(x + r, y + h)
        cr.curve_to(x, y + h, x, y + h, x, y + h - r)
        cr.line_to(x, y + r)
        cr.curve_to(x, y, x, y, x + r, y)

    def _outline_text(self, cr, w, h, size, text):
        cr.set_font_size(size)
        try:
            cr.select_font_face("Ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        except:
            pass
        te = cr.text_extents(text)
        cr.set_source_rgba(0.0, 0.0, 0.0, 1.0)
        cr.set_line_width(2.0)
        cx = w/2 - te[2]/2
        cy = h/2 - te[3]/2
        cr.move_to(cx, cy)
        cr.text_path(text)
        cr.stroke()
        cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        cr.move_to(cx, cy)
        cr.show_text(text)
