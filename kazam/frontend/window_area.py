# -*- coding: utf-8 -*-
#
#       window_area.py
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
import logging
logger = logging.getLogger("Window Area")

from gettext import gettext as _

from gi.repository import Gtk, GObject, Gdk

from kazam.backend.prefs import *

class AreaWindow(GObject.GObject):

    __gsignals__ = {
        "area-selected" : (GObject.SIGNAL_RUN_LAST,
                             None,
                               (),
                                ),
        "area-canceled" : (GObject.SIGNAL_RUN_LAST,
                             None,
                               (),
                                ),
    }

    def __init__(self):
        super(AreaWindow, self).__init__()
        logger.debug("Initializing area window.")
        self.window = Gtk.Window()
        self.window.set_title("Kazam Select")
        self.window.connect("configure-event", self.cb_configure_event)
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("draw", self.cb_draw)
        self.window.connect("key-press-event", self.cb_keypress_event)
        self.window.connect("button-press-event", self.cb_button_press_event)
        self.window.connect("show", self.cb_show)

        self.startx = 0
        self.starty = 0
        self.endx = 640
        self.endy = 480
        self.window.set_position(Gtk.WindowPosition.CENTER)

        self.width = self.endx - self.startx
        self.height = self.endy - self.starty
        self.window.set_default_geometry(self.width, self.height)

        self.window.set_border_width(30)
        self.window.set_app_paintable(True)
        self.window.set_has_resize_grip(False)
        self.window.set_resizable(True)
        self.window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.window.set_decorated(False)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_keep_above(True)
        self.screen = self.window.get_screen()
        self.visual = self.screen.get_rgba_visual()
        self.recording = False

        if self.visual is not None and self.screen.is_composited():
            logger.debug("Compositing window manager detected.")
            self.window.set_visual(self.visual)
            self.compositing = True
        else:
            self.compositing = False

    def cb_show(self, widget):
        if prefs.area:
            logger.debug("Old area defined at: X: {0}, Y: {1}, W: {2}, H: {3}".format(prefs.area[0],
                                                                                        prefs.area[1],
                                                                                        prefs.area[2],
                                                                                        prefs.area[3]))
            self.startx = prefs.area[0]
            self.starty = prefs.area[1]
            self.endx = prefs.area[2]
            self.endy = prefs.area[3]
            self.window.move(self.startx, self.starty)

    def cb_button_press_event(self, widget, event):
        (op, button) = event.get_button()
        if button == 1:
            # TODO: Lure someone into making this code a little less ugly ...
            if int(event.x) in range(0, 16) and int(event.y) in range(0,16):
                self.window.begin_resize_drag(Gdk.WindowEdge.NORTH_WEST, button,
                                              event.x_root, event.y_root, event.time)

            elif int(event.x) in range(self.width-16, self.width) and int(event.y) in range(0,16):
                self.window.begin_resize_drag(Gdk.WindowEdge.NORTH_EAST, button,
                                              event.x_root, event.y_root, event.time)

            elif int(event.x) in range(self.width-16, self.width) and int(event.y) in range(self.height-16,self.height):
                self.window.begin_resize_drag(Gdk.WindowEdge.SOUTH_EAST, button,
                                              event.x_root, event.y_root, event.time)

            elif int(event.x) in range(0, 16) and int(event.y) in range(self.height-16, self.height):
                self.window.begin_resize_drag(Gdk.WindowEdge.SOUTH_WEST, button,
                                              event.x_root, event.y_root, event.time)

            elif int(event.x) in range(self.width/2-8, self.width/2+8) and int(event.y) in range(0,16):
                self.window.begin_resize_drag(Gdk.WindowEdge.NORTH, button,
                                              event.x_root, event.y_root, event.time)

            elif int(event.x) in range(self.width/2-8, self.width/2+8) and int(event.y) in range(self.height-16, self.height):
                self.window.begin_resize_drag(Gdk.WindowEdge.SOUTH, button,
                                              event.x_root, event.y_root, event.time)

            elif int(event.x) in range(0, 16) and int(event.y) in range(self.height/2-8,self.height/2+8):
                self.window.begin_resize_drag(Gdk.WindowEdge.WEST, button,
                                              event.x_root, event.y_root, event.time)

            elif int(event.x) in range(self.width-16, self.width) and int(event.y) in range(self.height/2-8,self.height/2+8):
                self.window.begin_resize_drag(Gdk.WindowEdge.EAST, button,
                                              event.x_root, event.y_root, event.time)

            else:
                self.window.begin_move_drag(button, event.x_root, event.y_root, event.time)

    def cb_keypress_event(self, widget, event):
        (op, keycode) = event.get_keycode()
        if keycode == 36 or keycode == 104: # Enter
            self.window.set_default_geometry(self.width, self.height)
            (self.startx, self.starty) = self.window.get_position()
            self.endx = self.startx + self.width - 1
            self.endy = self.starty + self.height - 1
            self.recording = True
            self.window.input_shape_combine_region(None)
            #
            # When support for masked input is back, remove the hide() call.
            #
            self.window.hide()
            # self.window.queue_draw()
            self.emit("area-selected")
        elif keycode == 9: # ESC
            self.window.hide()
            self.emit("area-canceled")


    def cb_configure_event(self, widget, event):
        self.width = event.width
        self.height = event.height

    def cb_draw(self, widget, cr):
        w = self.width
        h = self.height
        #
        # Drawing a red rectangle around selected area would be extremely nice
        # however, cairo.Region is missing from GIR and from pycairo and
        # it is needed for input_shape_combine_region().
        # See: https://bugs.freedesktop.org/show_bug.cgi?id=44336
        #
        #if self.recording:
        #    cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        #    cr.set_operator(cairo.OPERATOR_SOURCE)
        #    cr.paint()
        #    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w , h)
        #    surface_ctx = cairo.Context(surface)
        #    surface_ctx.set_source_rgba(1.0, 1.0, 1.0, 0.0)
        #    surface_ctx.set_operator(cairo.OPERATOR_SOURCE)
        #    surface_ctx.paint()
        #    reg = Gdk.cairo_region_create_from_surface(surface)
        #    widget.input_shape_combine_region(reg)
        #    cr.move_to(0, 0)
        #    cr.set_source_rgb(1.0, 0.0, 0.0)
        #    cr.set_line_width(2.0)
        #    cr.rectangle(0, 0, w, h)
        #    cr.stroke()
        #    cr.set_operator(cairo.OPERATOR_OVER)
        #else:
        if self.compositing:
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.65)
        else:
            cr.set_source_rgb(0.5, 0.5, 0.5)

        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        if self.compositing:
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        else:
            cr.set_source_rgba(1.0, 1.0, 1.0)
        cr.set_line_width(6.0)
        cr.move_to(0, 0)
        cr.rectangle(0, 0, 16, 16)
        cr.rectangle(w-16, 0, 16, 16)
        cr.rectangle(0, h-16, 16, 16)
        cr.rectangle(w-16, h-16, 16, 16)
        cr.rectangle(w/2-8, 0, 16, 16)
        cr.rectangle(w/2-8, h-16, 16, 16)

        cr.rectangle(0, h/2-8, 16, 16)
        cr.rectangle(w-16, h/2-8, 16, 16)

        cr.fill()
        cr.set_source_rgb(0.65, 0.65, 0.65)
        cr.rectangle(0, 0, w, h)
        cr.stroke()
        cr.set_operator(cairo.OPERATOR_OVER)
        self._outline_text(cr, w, h, 30, _("Select area by resizing the rectangle"))
        self._outline_text(cr, w, h + 50, 26, _("Press ENTER to confirm or ESC to cancel"))
        self._outline_text(cr, w, h + 100, 20, "({0} x {1})".format(w, h))


    def _outline_text(self, cr, w, h, size, text):
        cr.set_font_size(size)
        try:
            cr.select_font_face("Ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        except:
            pass
        te = cr.text_extents(text)
        cr.set_line_width(2.0)
        cx = w/2 - te[2]/2
        cy = h/2 - te[3]/2
        if self.compositing:
            cr.set_source_rgba(0.4, 0.4, 0.4, 1.0)
        else:
            cr.set_source_rgb(0.4, 0.4, 0.4)

        cr.move_to(cx, cy)
        cr.text_path(text)
        cr.stroke()
        if self.compositing:
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        else:
            cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.move_to(cx, cy)
        cr.show_text(text)
