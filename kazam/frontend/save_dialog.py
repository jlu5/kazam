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
import logging
logger = logging.getLogger("Save Dialog")

from gi.repository import Gtk
from gettext import gettext as _

from kazam.backend.prefs import *
from kazam.backend.constants import *

def SaveDialog(title, old_path, codec, main_mode=MODE_SCREENCAST):
    logger.debug("Save dialog called.")
    dialog = Gtk.FileChooserDialog(title, None,
                                   Gtk.FileChooserAction.SAVE,
                                   (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                   _("Save"), Gtk.ResponseType.OK))

    if main_mode == MODE_SCREENCAST:
        dialog.set_current_name("{0}{1}".format(_("Untitled_Screencast"), CODEC_LIST[codec][3]))
    elif main_mode == MODE_SCREENSHOT:
        dialog.set_current_name(_("Untitled_Capture.png"))

    dialog.set_do_overwrite_confirmation(True)

    if old_path and os.path.isdir(old_path):
            dialog.set_current_folder(old_path)
    elif os.path.isdir(prefs.video_dest):
        dialog.set_current_folder(prefs.video_dest)

    dialog.show_all()
    #
    # In Oneiric Ocelot FileChooser dialog.run() will always report:
    # (kazam:4692): Gtk-WARNING **: Unable to retrieve the file info for...
    # This appears to be a bug in Gtk3 and it is fixed in Precise Pangolin.
    #
    result = dialog.run()
    old_path = dialog.get_current_folder()
    return dialog, result, old_path

