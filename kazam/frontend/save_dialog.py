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
from gettext import gettext as _
from gi.repository import Gtk

from kazam.backend.constants import *

def SaveDialog(title, codec):
    dialog = Gtk.FileChooserDialog(title, None,
                                   Gtk.FileChooserAction.SAVE,
                                   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                   _("Save"), Gtk.ResponseType.OK))

    if codec == CODEC_VP8:
        dialog.set_current_name("%s.webm" % _("Untitled_Screencast"))
    elif codec == CODEC_H264:
        dialog.set_current_name("%s.mkv" % _("Untitled_Screencast"))

    dialog.set_do_overwrite_confirmation(True)

    # Try to set the default folder to be ~/Videos, otherwise
    # ~/Documents, otherwise ~/
    video_path = os.path.expanduser("~/Videos/")
    documents_path = os.path.expanduser("~/Documents/")
    home_path = os.path.expanduser("~/")

    if os.path.isdir(video_path):
        dialog.add_shortcut_folder(video_path)
        dialog.set_current_folder(video_path)
    elif os.path.isdir(documents_path):
        dialog.set_current_folder(documents_path)
    elif os.path.isdir(home_path):
        dialog.set_current_folder(home_path)

    dialog.show_all()
    #
    # In Oneiric Ocelot FileChooser dialog.run() will always report:
    # (kazam:4692): Gtk-WARNING **: Unable to retrieve the file info for...
    # This appears to be a bug in Gtk3 and it is fixed in Precise Pangolin.
    #
    result = dialog.run()
    return dialog, result

