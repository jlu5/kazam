# -*- coding: utf-8 -*-
#
#       save_dialog.py
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
from gi.repository import Gtk
from gettext import gettext as _
from xdg.BaseDirectory import xdg_config_home

from kazam.backend.constants import *

def SaveDialog(title, old_path, codec):
    dialog = Gtk.FileChooserDialog(title, None,
                                   Gtk.FileChooserAction.SAVE,
                                   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                   _("Save"), Gtk.ResponseType.OK))

    if codec == CODEC_VP8:
        dialog.set_current_name("%s.webm" % _("Untitled_Screencast"))
    elif codec == CODEC_H264:
        dialog.set_current_name("%s.mkv" % _("Untitled_Screencast"))

    dialog.set_do_overwrite_confirmation(True)

    # Try to set the default folder to be previously selected path
    # if there was one otherwise try with ~/Videos, ~/Documents
    # and finally ~/
    paths = {}
    try:
        f = open(os.path.join(xdg_config_home, "user-dirs.dirs"))
        for la in f:
            if la.startswith("XDG_VIDEOS") or la.startswith("XDG_DOCUMENTS"):
                (idx, val) = la.strip()[:-1].split('="')
                paths[idx] = os.path.expandvars(val)
    except:
        paths['XDG_VIDEOS_DIR'] = os.path.expanduser("~/Videos/")
        paths['XDG_DOCUMENTS_DIR'] = os.path.expanduser("~/Documents/")

    paths['HOME_DIR'] = os.path.expandvars("$HOME")

    if old_path and os.path.isdir(old_path):
            dialog.set_current_folder(old_path)
    elif os.path.isdir(paths['XDG_VIDEOS_DIR']):
        dialog.set_current_folder(paths['XDG_VIDEOS_DIR'])
    elif os.path.isdir(paths['XDG_DOCUMENTS_DIR']):
        dialog.set_current_folder(paths['XDG_DOCUMENTS_DIR'])
    elif os.path.isdir(paths['HOME_DIR']):
        dialog.set_current_folder(paths['HOME_DIR'])

    dialog.show_all()
    #
    # In Oneiric Ocelot FileChooser dialog.run() will always report:
    # (kazam:4692): Gtk-WARNING **: Unable to retrieve the file info for...
    # This appears to be a bug in Gtk3 and it is fixed in Precise Pangolin.
    #
    result = dialog.run()
    old_path = dialog.get_current_folder()
    return dialog, result, old_path

