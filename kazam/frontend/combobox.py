# -*- coding: utf-8 -*-
#
#       combobox.py
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

import os
import subprocess
from gettext import gettext as _
from xdg.DesktopEntry import DesktopEntry
from gi.repository import Gtk, GdkPixbuf, GObject

class EditComboBox(Gtk.ComboBox):

    KDENLIVE_VERSION = [0,8]
    EDITORS = {
               "/usr/share/applications/openshot.desktop":[],
               "/usr/share/applications/pitivi.desktop":["-i", "-a"],
               "/usr/share/applications/avidemux-gtk.desktop":[],
               "/usr/share/applications/kde4/kdenlive.desktop":["-i"],
              }

    def __init__(self, icons):
        Gtk.ComboBox.__init__(self)
        self.icons = icons
        self.empty = True
        cr_pixbuf = Gtk.CellRendererPixbuf()
        self.pack_start(cr_pixbuf, True)
        self.add_attribute(cr_pixbuf, 'pixbuf', 0)
        cr_text = Gtk.CellRendererText()
        self.pack_start(cr_text, True)
        self.add_attribute(cr_text, 'text', 1)

        self.box_model = Gtk.ListStore(GdkPixbuf.Pixbuf, str,
                                       GObject.TYPE_PYOBJECT,
                                       GObject.TYPE_PYOBJECT
                                      )
        self.set_model(self.box_model)
        self._populate()
        self.set_active(0)
        self.set_sensitive(True)
        self.show()

    def get_active_value(self):
        i = self.get_active()
        model = self.get_model()
        model_iter = model.get_iter(i)
        return (model.get_value(model_iter, 2),
                model.get_value(model_iter, 3))

    def _populate(self):

        args = []
#        command = "kazam"
#        name = _("Kazam Screencaster")
#        icon_name = "kazam"
#        self._add_item(icon_name, name, command, args)

        for item in self.EDITORS:
            if os.path.isfile(item):
                args = self.EDITORS[item]
                desktop_entry = DesktopEntry(item)
                command = desktop_entry.getExec()

                # For .desktop files with ' %U' or ' # %F'
                command = command.split(" ")[0]

                name = desktop_entry.getName()
                icon_name = desktop_entry.getIcon()

                if command == "kdenlive":
                    p = subprocess.Popen([command, "-v"], stdout=subprocess.PIPE)
                    output = p.communicate()[0]
                    version = output.strip().split("\n")[-1].replace("Kdenlive: ", "").split(".")
                    if self.version_is_gte(self.KDENLIVE_VERSION, version):
                        self._add_item(icon_name, name, command, args)
                else:
                    self._add_item(icon_name, name, command, args)

        if len(self.get_model()) == 0:
            self.emtpy = True
        else:
            self.empty = False



    def _add_item(self, icon_name, name, command, args):
        liststore = self.get_model()
        try:
            pixbuf = self.icons.load_icon(icon_name, 16, Gtk.IconLookupFlags.GENERIC_FALLBACK)
        except:
            pixbuf = self.icons.load_icon("application-x-executable", 16, Gtk.IconLookupFlags.GENERIC_FALLBACK)

        liststore.append([pixbuf, name, command, args])
