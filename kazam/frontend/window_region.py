# -*- coding: utf-8 -*-
#
#       window_region.py
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
logger = logging.getLogger("Window Region")

from gettext import gettext as _

from gi.repository import Gtk, GObject, Gdk

class RegionWindow(GObject.GObject):

    __gsignals__ = {
        "region-selected" : (GObject.SIGNAL_RUN_LAST,
                             None,
                               (),
                                ),
        "region-canceled" : (GObject.SIGNAL_RUN_LAST,
                             None,
                               (),
                                ),
    }

    def __init__(self, region = None):
        super(RegionWindow, self).__init__()
        logger.debug("Initializing region window.")
        self.window = Gtk.Window()
        self.window.connect("configure-event", self.cb_configure_event)
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("draw", self.cb_draw)
        self.window.connect("key-press-event", self.cb_keypress_event)
        self.window.connect("button-press-event", self.cb_button_press_event)
        self.window.connect("button-release-event", self.cb_button_release_event)
        self.window.connect("motion-notify-event", self.cb_motion_notify_event)

        if region:
            logger.debug("Old region defined at: X: {0}, Y: {1}, W: {2}, H: {3}".format(region[0],
                                                                                          region[1],
                                                                                          region[2],
                                                                                          region[3]))
            self.startx = region[0]
            self.starty = region[1]
            self.endx = region[2]
            self.endy = region[3]
        else:
            self.startx = 0
            self.starty = 0
            self.endx = 0
            self.endy = 0

        self.width = self.endx - self.startx
        self.height = self.endy - self.starty
        self.window.set_default_geometry(0,0)

        self.window.set_border_width(1)
        self.window.set_app_paintable(True)
        self.window.set_has_resize_grip(False)
        self.window.set_resizable(True)
        self.window.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK | Gdk.EventMask.POINTER_MOTION_MASK)
        self.window.set_decorated(False)
        self.window.set_property("skip-taskbar-hint", True)
        self.window.set_keep_above(True)
        self.window.fullscreen()
        self.screen = self.window.get_screen()
        self.visual = self.screen.get_rgba_visual()
        self.recording = False

        if self.visual is not None and self.screen.is_composited():
            logger.debug("Compositing window manager detected.")
            self.window.set_visual(self.visual)
            self.compositing = True
        else:
            self.compositing = False

        self.window.show_all()


    def cb_button_press_event(self, widget, event):
        (op, button) = event.get_button()
        if button == 1:
            # Remember the starting coordinates! Remember! ;)
            self.startx = event.x
            self.starty = event.y
            self.endx = self.startx
            self.endy = self.starty

    def cb_button_release_event(self, widget, event):
        (op, button) = event.get_button()
        if button == 1:
            # Remember the ending coordinates! Remember! ;)
            self.endx = event.x
            self.endy = event.y


    def cb_motion_notify_event(self, widget, event):
        if event.state & Gdk.ModifierType.BUTTON1_MASK:
            self.endx = event.x
            self.endy = event.y
            #
            # Fix. This. :)
            #
            self.width = abs(self.startx - self.endx)
            self.height = abs(self.starty - self.endy)
            self.window.queue_draw()

    def cb_keypress_event(self, widget, event):
        (op, keycode) = event.get_keycode()
        if keycode == 36 or keycode == 104: # Enter
            self.window.set_default_geometry(self.width, self.height)
            (self.startx, self.starty) = self.window.get_position()
            self.endx = self.startx + self.width - 1
            self.endy = self.starty + self.height - 1
            self.recording = True
            self.window.input_shape_combine_region(None)
            self.window.hide()
            self.emit("region-selected")
        elif keycode == 9: # ESC
            self.window.hide()
            self.emit("region-canceled")


    def cb_configure_event(self, widget, event):
        self.screen_width = event.width
        self.screen_height = event.height
        print self.screen_height

    def cb_draw(self, widget, cr):
        w = self.screen_width
        h = self.screen_height

        if self.compositing:
            cr.set_source_rgba(0.0, 0.0, 0.0, 0.65)
        else:
            cr.set_source_rgb(0.5, 0.5, 0.5)

        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        if self.compositing:
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        else:
            cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.set_line_width(2.0)

        cr.fill()
        cr.set_source_rgb(0.65, 0.65, 0.65)
        cr.rectangle(0, 0, w, h)
        cr.stroke()

        if self.compositing:
            cr.set_source_rgba(0, 0, 0, 0.0)
        else:
            cr.set_source_rgb(.8, .8, .8)

        cr.rectangle(self.startx, self.starty, self.width, self.height)
        cr.fill()
        cr.set_operator(cairo.OPERATOR_OVER)

        self._outline_text(cr, w, h, 30, _("Select recording region with the mouse."))
        self._outline_text(cr, w, h + 50, 26, _("Press ENTER to confirm or ESC to cancel."))
        self._outline_text(cr, w, h + 100, 20, "({0} x {1})".format(int(self.width), int(self.height)))

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
