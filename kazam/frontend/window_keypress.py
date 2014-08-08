# -*- coding: utf-8 -*-
#
#       window_keypress.py
#
#       Copyright 2014 David Klasinc <bigwhale@lubica.net>
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

import re
import cairo
import logging
logger = logging.getLogger("Window Keypress")

from gi.repository import Gtk, GObject, Gdk, GdkX11, GLib
from kazam.backend.prefs import *


class KeypressWindow(GObject.GObject):
    def __init__(self, show_window=True):
        super(KeypressWindow, self).__init__()
        logger.debug("Initializing Keypress window.")

        self.window = Gtk.Window(Gtk.WindowType.TOPLEVEL)
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.connect("draw", self.cb_draw)
        self.window.connect("screen-changed", self.onScreenChanged)
        self.window.set_app_paintable(True)
        self.window.set_decorated(False)
        self.window.set_title("CountdownWindow")
        self.window.set_keep_above(True)
        self.window.set_focus_on_map(False)
        self.window.set_accept_focus(False)
        self.window.set_skip_pager_hint(True)
        self.window.set_skip_taskbar_hint(True)

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
            logger.warning("Compositing window manager not found, expect the unexpected.")
            self.compositing = False

        # make window click-through, this needs pycairo 1.10.0 for python3
        # to work
        rect = cairo.RectangleInt(0, 0, 1, 1)
        region = cairo.Region(rect)
        if (not region.is_empty()):
            self.window.input_shape_combine_region(None)
            self.window.input_shape_combine_region(region)

        # make sure that gtk-window opens with a RGBA-visual
        self.onScreenChanged(self.window, None)
        self.window.set_opacity(0)
        self.window.realize()
        self.window.set_type_hint(Gdk.WindowTypeHint.DOCK)
        transparent = Gdk.RGBA(0.0, 0.0, 0.0, 0.0)
        gdkwindow = self.window.get_window()
        gdkwindow.set_background_rgba(transparent)

        screen = HW.screens[prefs.current_screen]
        width = 1
        height = 1
        self.window.set_size_request(width, height)
        self.window.set_default_geometry(width, height)
        self.window.move(int(screen['width'] / 2 - width / 2), screen['height'] - 150)

        self.alpha = 0

        self.buffer = ""

        self._in = False
        self._out = False
        self.f_t = None
        self.previous_key = None
        self.keys_pressed = False
        self.window.show_all()

        self.modifiers = [False, False, False, False]

    #
    # Rewrite this
    #
    def show(self, key, event):
        logger.debug("Current buffer: {}".format(self.buffer))
        if event == 'Press':
            if key != self.previous_key:
                if self.f_t:
                    GLib.source_remove(self.f_t)
                    self.f_t = None
                if key.startswith('Shift'):
                    self.modifiers[K_SHIFT] = True
                elif key.startswith('Control'):
                    self.modifiers[K_CTRL] = True
                elif key.startswith('Super'):
                    self.modifiers[K_SUPER] = True
                elif key.startswith('Alt'):
                    self.modifiers[K_ALT] = True
                else:
                        self.buffer += key
                        self.previous_key = key
                #
                # Show keys only if modifiers are pressed
                #
                if True in self.modifiers:
                    self._in = True
                    # self.f_t = GLib.timeout_add(1300, self.fade_out, self.window)
                    self.window.queue_draw()

        elif event == 'Release':
            if key.startswith('Shift'):
                self.modifiers[K_SHIFT] = False
            elif key.startswith('Control'):
                self.modifiers[K_CTRL] = False
            elif key.startswith('Super'):
                self.modifiers[K_SUPER] = False
            elif key.startswith('Alt'):
                self.modifiers[K_ALT] = False

            if not all(self.modifiers) and not any(self.modifiers):  # Fadeout if none of the modifiers are pressed
                logger.debug("Fadeout!")
                self.fade_out(self.window)

    def onScreenChanged(self, widget, oldScreen):
        screen = widget.get_screen()
        visual = screen.get_rgba_visual()
        if visual is None:
            visual = screen.get_system_visual()
        widget.set_visual(visual)

    def fade(self, widget):
        widget.queue_draw()
        return True

    def fade_out(self, widget):
        self._out = True
        self.buffer = ""
        self.previous_key = None
        widget.queue_draw()
        self.modifiers[K_SHIFT] = False
        self.modifiers[K_CTRL] = False
        self.modifiers[K_SUPER] = False
        self.modifiers[K_ALT] = False
        return True

    def cb_draw(self, widget, cr):
        buf = " + ".join([i[0] for i in zip(KEY_STRINGS, self.modifiers) if i[1]])
        buf = " ".join((buf, self.buffer))

        w, h = self._text_size(cr, 20, buf)

        self.window.set_size_request(w + 20, 50)
        self.window.set_default_geometry(w + 20, 50)
        Ww, Wh = widget.get_size()
        widget.set_opacity(self.alpha)
        cr.set_source_rgba(.4, .4, .4, .7)
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        self._outline_text(cr, 10, Wh - 15, 20, buf)

        if self._in:
            if self.alpha >= 1:
                self._in = False
                return False
            else:
                self.alpha += 0.10
                self.f_ret = GLib.timeout_add(2, self.fade, self.window)
            return True

        elif self._out:
            if self.alpha <= 0:
                self._out = False
                return False
            else:
                self.alpha -= 0.10
                self.f_ret = GLib.timeout_add(2, self.fade, self.window)
            return True

    def _outline_text(self, cr, x, y, size, text):
        cr.set_font_size(size)
        try:
            cr.select_font_face("Ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        except:  # Think of what to do here ...
            pass
        cr.set_line_width(2.0)
        if self.compositing:
            cr.set_source_rgba(0.4, 0.4, 0.4, 1.0)
        else:
            cr.set_source_rgb(0.4, 0.4, 0.4)

        cr.move_to(x, y)
        cr.text_path(text)
        cr.stroke()
        if self.compositing:
            cr.set_source_rgba(1.0, 1.0, 1.0, 1.0)
        else:
            cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.move_to(x, y)
        cr.show_text(text)

    def _text_size(self, cr, size, text):
        cr.set_font_size(size)
        try:
            cr.select_font_face("Ubuntu", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        except:  # Think of what to do here ...
            pass
        te = cr.text_extents(text)
        return (te[2], te[3])
