# -*- coding: utf-8 -*-
#
#       indicator.py
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

import locale
import gettext
import logging
#import keybinder

from gettext import gettext as _
from gi.repository import Gtk, GObject

class KazamSuperIndicator(GObject.GObject):

    __gsignals__ = {
        "pause-requested" : (GObject.SIGNAL_RUN_LAST,
                                   None,
                                   (),
                                  ),
        "unpause-requested" : (GObject.SIGNAL_RUN_LAST,
                                   None,
                                   (),
                                  ),
        "quit-requested" : (GObject.SIGNAL_RUN_LAST,
                                  None,
                                   (),
                                  ),
        "show-requested" : (GObject.SIGNAL_RUN_LAST,
                                  None,
                                   (),
                                  ),
        "recording-done" : (GObject.SIGNAL_RUN_LAST,
                                  None,
                                   (),
                                  ),
    }

    def __init__(self):
        super(KazamSuperIndicator, self).__init__()

        self.menu = Gtk.Menu()

        self.menuitem_pause = Gtk.CheckMenuItem(_("Pause recording"))
        self.menuitem_pause.set_sensitive(False)
        self.menuitem_pause.connect("activate", self.on_menuitem_pause_activate)
        self.menuitem_finish = Gtk.MenuItem(_("Finish recording"))
        self.menuitem_finish.set_sensitive(False)
        self.menuitem_finish.connect("activate", self.on_menuitem_finish_activate)
        self.menuitem_separator = Gtk.SeparatorMenuItem()
        self.menuitem_separator2 = Gtk.SeparatorMenuItem()
        self.menuitem_show = Gtk.MenuItem(_("Record setup"))
        self.menuitem_show.connect("activate", self.on_menuitem_show_activate)
        self.menuitem_quit = Gtk.MenuItem(_("Quit"))
        self.menuitem_quit.connect("activate", self.on_menuitem_quit_activate)
        self.menu.append(self.menuitem_pause)
        self.menu.append(self.menuitem_finish)
        self.menu.append(self.menuitem_separator)
        self.menu.append(self.menuitem_show)
        self.menu.append(self.menuitem_separator2)
        self.menu.append(self.menuitem_quit)
        self.menu.show_all()

        # Set keyboard shortcuts
        #pause_shortcut = config.get("keyboard_shortcuts", "pause")
        #finish_shortcut = config.get("keyboard_shortcuts", "finish")
        #quit_shortcut = config.get("keyboard_shortcuts", "quit")
        #keybinder.bind(pause_shortcut, self.on_pause_shortcut_pressed_)
        #keybinder.bind(finish_shortcut, self.on_finish_shortcut_pressed_)
        #keybinder.bind(quit_shortcut, self.on_quit_shortcut_pressed_)

    def on_menuitem_pause_activate(self, menuitem_pause):
        if menuitem_pause.get_active():
            self.emit("pause-requested")
        else:
            self.emit("unpause-requested")

    def on_menuitem_finish_activate(self):
        self.menuitem_pause.set_sensitive(False)
        self.menuitem_finish.set_sensitive(False)
        self.menuitem_show.set_sensitive(True)
        self.menuitem_pause.set_active(False)
        self.emit("recording-done")

    def on_menuitem_quit_activate(self, menuitem_quit):
        self.emit("quit-requested")

    def on_menuitem_show_activate(self, menuitem_show):
        self.emit("show-requested")

    def count(self, count):
        pass

    def start_recording(self):
        self.menuitem_pause.set_sensitive(True)
        self.menuitem_finish.set_sensitive(True)
        self.menuitem_show.set_sensitive(False)

    def on_pause_shortcut_pressed_(self):
        self.on_menuitem_pause_activate(self.menuitem_pause)
        self.menuitem_pause.set_active(not self.menuitem_pause.get_active())

    def on_quit_shortcut_pressed_(self):
        self.on_menuitem_quit_activate(self.menuitem_quit)

    def on_finish_shortcut_pressed_(self):
       self.on_menuitem_finish_activate(self.menuitem_finish)


try:
    from gi.repository import AppIndicator3

    class KazamIndicator(KazamSuperIndicator):

        def __init__(self):
            super(KazamIndicator, self).__init__()

            self.indicator = AppIndicator3.Indicator.new("kazam",
                                "kazam-stopped",
                                AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
            self.indicator.set_menu(self.menu)
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.indicator.set_attention_icon("kazam-recording")
            self.indicator.set_icon("kazam-stopped")

        def on_menuitem_pause_activate(self, menuitem_pause):
            KazamSuperIndicator.on_menuitem_pause_activate(self, menuitem_pause)
            if menuitem_pause.get_active():
                self.indicator.set_attention_icon("kazam-paused")
                logging.info("Recording paused")
            else:
                self.indicator.set_attention_icon("kazam-recording")
                logging.info("Recording started again")

        def on_menuitem_finish_activate(self, menuitem_finish):
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            KazamSuperIndicator.on_menuitem_finish_activate(self)

        def count(self, count):
            self.indicator.set_attention_icon("kazam-countdown-%s" % count)

        def start_recording(self):
            KazamSuperIndicator.start_recording(self)
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ATTENTION)

except ImportError:
    pass

#    class KazamIndicator(KazamSuperIndicator):
#
#        def __init__(self, config):
#            super(KazamIndicator, self).__init__(config)
#
#            self.indicator = gtk.StatusIcon()
#            self.indicator.set_from_icon_name("kazam-countdown-5")
#            self.indicator.connect("popup-menu", self.on_status_icon_right_click_event)

#        def on_status_icon_right_click_event(self, icon, button, time):
#            self.menu.popup(None, None, gtk.status_icon_position_menu,
#                            button, time, self.indicator)

#        def on_menuitem_pause_activate(self, menuitem_pause):
#            KazamSuperIndicator.on_menuitem_pause_activate(self,
#                                                        menuitem_pause)
#            if menuitem_pause.get_active():
#                self.indicator.set_from_icon_name("kazam-paused")
#                logging.info("Recording paused")
#            else:
#                self.indicator.set_from_icon_name("kazam-recording")
#                logging.info("Recording started again")

#        def on_menuitem_finish_activate(self, menuitem_finish):
#            KazamSuperIndicator.on_menuitem_finish_activate(self)
#            self.indicator.set_visible(False)

#        def count(self, count):
#            self.indicator.set_from_icon_name("kazam-countdown-%s" % count)

#        def start_recording(self):
#            KazamSuperIndicator.start_recording(self)
#            self.indicator.set_from_icon_name("kazam-recording")

