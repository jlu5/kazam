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

import time
import cairo
import logging
logger = logging.getLogger("Window Select")

from gettext import gettext as _

from gi.repository import Gtk, GObject, Gdk, Wnck, GdkX11

from kazam.backend.constants import *
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
        logger.debug("Initializing select window.")

        self.startx = 0
        self.starty = 0
        self.endx = 0
        self.endy = 0
        self.height = 0
        self.width = 0

        self.window = Gtk.Window()
        self.box = Gtk.Box()
        self.drawing = Gtk.DrawingArea()
        self.box.pack_start(self.drawing, True, True, 0)
        self.drawing.set_size_request(500, 500)
        self.window.add(self.box)

        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("key-press-event", self.cb_keypress_event)

        self.drawing.connect("draw", self.cb_draw)
        self.drawing.connect("motion-notify-event", self.cb_draw_motion_notify_event)
        self.drawing.connect("button-press-event", self.cb_draw_button_press_event)
        self.drawing.connect("leave-notify-event", self.cb_leave_notify_event)
        self.drawing.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.POINTER_MOTION_HINT_MASK | Gdk.EventMask.LEAVE_NOTIFY_MASK)

        self.window.set_border_width(0)
        self.window.set_app_paintable(True)
        self.window.set_has_resize_grip(False)
        self.window.set_resizable(True)
        self.window.set_decorated(False)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_keep_above(True)
        self.screen = self.window.get_screen()
        self.visual = self.screen.get_rgba_visual()

        self.disp = GdkX11.X11Display.get_default()
        self.dm = Gdk.Display.get_device_manager(self.disp)
        self.pntr_device = self.dm.get_client_pointer()

        if self.visual is not None and self.screen.is_composited():
            logger.debug("Compositing window manager detected.")
            self.window.set_visual(self.visual)
            self.compositing = True
        else:
            self.compositing = False

        (scr, x, y) = self.pntr_device.get_position()
        cur = scr.get_monitor_at_point(x, y)
        self.window.move(HW.screens[cur]['x'],
                         HW.screens[cur]['y'])
        self.window.fullscreen()

        crosshair_cursor = Gdk.Cursor(Gdk.CursorType.CROSSHAIR)
        self.last_cursor = Gdk.Cursor(Gdk.CursorType.LEFT_PTR)
        self.gdk_win = self.window.get_root_window()
        self.gdk_win.set_cursor(crosshair_cursor)

    def cb_draw_motion_notify_event(self, widget, event):
        (state, x, y, mask) = event.window.get_device_position(self.pntr_device)
        if mask & Gdk.ModifierType.BUTTON1_MASK:
            self.endx = int(event.x)
            self.endy = int(event.y)
            self.width  = self.endx - self.startx
            self.height = self.endy - self.starty
        widget.queue_draw()
        return True

    def cb_draw_button_press_event(self, widget, event):
        self.startx = int(event.x)
        self.starty = int(event.y)
        self.endx = 0
        self.endy = 0
        self.width  = 0
        self.height = 0

    def cb_leave_notify_event(self, widget, event):
        (scr, x, y) = self.pntr_device.get_position()
        cur = scr.get_monitor_at_point(x, y)
        self.window.unfullscreen()
        self.window.move(HW.screens[cur]['x'],
                         HW.screens[cur]['y'])
        self.window.fullscreen()
        logger.debug("Move to X: {0} Y: {1}".format(HW.screens[cur]['x'], HW.screens[cur]['y']))
        return True

    def cb_keypress_event(self, widget, event):
        (op, keycode) = event.get_keycode()
        self.gdk_win.set_cursor(self.last_cursor)
        if keycode == 36 or keycode == 104: # Enter
            self.window.hide()
            self.width = abs(self.width)
            self.height = abs(self.height)
            self.emit("area-selected")
        elif keycode == 9: # ESC
            self.window.hide()
            self.emit("area-canceled")

    def cb_draw(self, widget, cr):
        (w, h) = self.window.get_size()

        if self.compositing:
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.45)
        else:
            cr.set_source_rgb(0.5, 0.5, 0.5)

        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()

        cr.set_operator(cairo.OPERATOR_SOURCE)

        # Draw the selection area
        cr.move_to(self.startx, self.starty)
        cr.set_source_rgb(1.0, 0.0, 0.0)
        cr.rectangle(self.startx, self.starty, self.width, self.height)
        cr.stroke()

        if self.compositing:
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.0)
        else:
            cr.set_source_rgb(0.0, 0.0, 0.0)

        cr.rectangle(self.startx, self.starty, self.width, self.height)
        cr.fill()

        cr.set_operator(cairo.OPERATOR_OVER)

        self._outline_text(cr, w, h, 30, _("Select an area by clicking and dragging."))
        self._outline_text(cr, w, h + 50, 26, _("Press ENTER to confirm or ESC to cancel"))

        self._outline_text(cr, w, h + 100, 20, "({0} x {1})".format(abs(self.height), abs(self.height)))
        cr.set_operator(cairo.OPERATOR_SOURCE)

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
