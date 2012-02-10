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

import logging

from gettext import gettext as _
from gi.repository import Gtk, GObject

class KazamSuperIndicator(GObject.GObject):

    __gsignals__ = {
        "pause-request" : (GObject.SIGNAL_RUN_LAST,
                                   None,
                                   (),
                                  ),
        "unpause-request" : (GObject.SIGNAL_RUN_LAST,
                                   None,
                                   (),
                                  ),
        "quit-request" : (GObject.SIGNAL_RUN_LAST,
                                  None,
                                   (),
                                  ),
        "show-request" : (GObject.SIGNAL_RUN_LAST,
                                  None,
                                   (),
                                  ),
        "stop-request" : (GObject.SIGNAL_RUN_LAST,
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

    def on_menuitem_pause_activate(self, menuitem):
        if self.menuitem_pause.get_active():
            self.emit("pause-request")
        else:
            self.emit("unpause-request")

    def on_menuitem_finish_activate(self, menuitem):
        self.menuitem_pause.set_sensitive(False)
        self.menuitem_finish.set_sensitive(False)
        self.menuitem_show.set_sensitive(True)
        self.menuitem_pause.set_active(False)
        self.menuitem_quit.set_sensitive(True)
        self.emit("stop-request")

    def on_menuitem_quit_activate(self, menuitem):
        self.emit("quit-request")

    def on_menuitem_show_activate(self, menuitem):
        self.emit("show-request")

    def start_recording(self):
        self.menuitem_pause.set_sensitive(True)
        self.menuitem_finish.set_sensitive(True)
        self.menuitem_show.set_sensitive(False)
        self.menuitem_quit.set_sensitive(False)

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

        def on_menuitem_pause_activate(self, menuitem):
            if menuitem.get_active():
                self.indicator.set_attention_icon("kazam-paused")
                logging.info("Recording paused")
            else:
                self.indicator.set_attention_icon("kazam-recording")
                logging.info("Recording started again")
            KazamSuperIndicator.on_menuitem_pause_activate(self, menuitem)

        def on_menuitem_finish_activate(self, menuitem):
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            KazamSuperIndicator.on_menuitem_finish_activate(self, menuitem)

        def start_recording(self):
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ATTENTION)
            KazamSuperIndicator.start_recording(self)

except ImportError:
    #
    # AppIndicator failed to import, not running Ubuntu?
    # Fallback to Gtk.StatusIcon.
    #
    class KazamIndicator(KazamSuperIndicator):

        def __init__(self):
            super(KazamIndicator, self).__init__()

            self.indicator = Gtk.StatusIcon()
            self.indicator.set_from_icon_name("kazam-stopped")
            self.indicator.connect("popup-menu", self.cb_indicator_popup_menu)
            self.indicator.connect("activate", self.cb_indicator_activate)

        def cb_indicator_activate(self, widget):
            def position(menu, widget):
		        return (Gtk.StatusIcon.position_menu(self.menu, widget))
            self.menu.popup(None, None, position, self.indicator, 0, Gtk.get_current_event_time())

        def cb_indicator_popup_menu(self, icon, button, time):
            def position(menu, icon):
		        return (Gtk.StatusIcon.position_menu(self.menu, icon))
            self.menu.popup(None, None, position, self.indicator, button, time)

        def on_menuitem_finish_activate(self, menuitem):
            self.indicator.set_from_icon_name("kazam-stopped")
            KazamSuperIndicator.on_menuitem_finish_activate(self, menuitem)

        def on_menuitem_pause_activate(self, menuitem):
            if menuitem.get_active():
                self.indicator.set_from_icon_name("kazam-paused")
                logging.info("Recording paused")
            else:
                self.indicator.set_from_icon_name("kazam-recording")
                logging.info("Recording started again")
            KazamSuperIndicator.on_menuitem_pause_activate(self, menuitem)

        def start_recording(self):
            self.indicator.set_from_icon_name("kazam-recording")
            KazamSuperIndicator.start_recording(self)

