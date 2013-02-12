# -*- coding: utf-8 -*-
#
#       window_select.py
#
#       Copyright 2012 David Klasinc <bigwhale@lubica.net>
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
import logging
logger = logging.getLogger("Outline Window")

from gi.repository import Gtk, GObject, Gdk, Wnck, GdkX11

from kazam.backend.constants import *


class OutlineWindow(GObject.GObject):

    def __init__(self, x, y, w, h):
        super(OutlineWindow, self).__init__()
        logger.debug("Initializing outline window.")
        print ("X: {0} Y: {1} W: {2} H: {3}".format(x, y, w, h))
        self.x = x - 1
        self.y = y - 1
        self.w = w + 3
        if y > 23:
            self.h = h + 3
        else:
            self.no_top = True
            self.h = h - 23 + y
        print ("X: {0} Y: {1} W: {2} H: {3}".format(self.x, self.y, self.w, self.h))
        self.window = Gtk.Window()

        self.window.connect("draw", self.cb_draw)

        self.window.set_border_width(0)
        self.window.set_app_paintable(True)
        self.window.set_has_resize_grip(False)
        self.window.set_resizable(True)
        self.window.set_decorated(False)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_keep_above(True)

        self.screen = self.window.get_screen()
        print (self.screen.get_number())
        self.visual = self.screen.get_rgba_visual()

        self.disp = GdkX11.X11Display.get_default()
        self.dm = Gdk.Display.get_device_manager(self.disp)
        self.pntr_device = self.dm.get_client_pointer()

        if self.visual is not None and self.screen.is_composited():
            logger.debug("Compositing window manager detected.")
            self.window.set_visual(self.visual)
            self.compositing = True
        else:
            logger.warning("Compositing window manager not found, expect the unexpected.")
            self.compositing = False

        self.window.move(self.x, self.y)
        self.window.set_default_geometry(self.w, self.h)
        (x, y) = self.window.get_position()
        (w, h) = self.window.get_size()
        print ("Given: X: {0} Y: {1} W: {2} H: {3}".format(x, y, w, h))
        self.window.show_all()

    def show(self):
        self.window.show_all()

    def hide(self):
        (x, y) = self.window.get_position()
        (w, h) = self.window.get_size()
        self.window.hide()

    def cb_draw(self, widget, cr):
        cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.w, self.h)
        surface_ctx = cairo.Context(surface)
        surface_ctx.set_source_rgba(1.0, 1.0, 1.0, 0.0)
        surface_ctx.set_operator(cairo.OPERATOR_SOURCE)
        surface_ctx.paint()
        reg = Gdk.cairo_region_create_from_surface(surface)
        widget.input_shape_combine_region(reg)
        cr.move_to(0, 0)
        cr.set_source_rgb(1.0, 0.0, 0.0)
        cr.set_line_width(2.0)

        #
        # Seriously?
        # The thing is, windows cannot overlap Panel or Launcher, so if your Launcher is 49 pixels wide and you panel
        # is 24 pixels high, you'll be just fine. Until I can find a way to detect those numbers.
        # Also, I should make this code Ubuntu only.
        #
        if self.y > 23:
            cr.line_to(self.w, 0)
        else:
            cr.move_to(self.w, 0)
        if self.x + self.w < HW.screens[self.screen.get_number()]['width']:
            cr.line_to(self.w, self.h)
        else:
            cr.move_to(self.w, self.h)
        if self.y + self.h < HW.screens[self.screen.get_number()]['height']:
            cr.line_to(0, self.h)
        else:
            cr.move_to(0, self.h)
        if self.x > 49:
            cr.line_to(0, 0)

        cr.stroke()
        cr.set_operator(cairo.OPERATOR_OVER)

