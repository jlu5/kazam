# -*- coding: utf-8 -*-
#
#       __init__.py
#
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

from gi.repository import GObject

class UploadSuperSource(GObject.GObject):

    ICON_LARGE = None
    ICON_SMALL = None
    NAME = None
    REGISTER_URL = None

    META = {}

    FFMPEG_OPTIONS = []
    FFMPEG_FILE_EXTENSION = ""

    def __init__(self):
        self.authentication = False
        super(UploadSuperSource, self).__init__()

    ###

    def login_pre(self, username, password):
        """Actions before login"""

    def login_in(self):
        """Actions in login"""

    def login_post(self):
        """Actions after login"""

    ###

    def upload_pre(self):
        """Actions before upload"""

    def upload_in(self):
        """Actions in upload"""

    def upload_post(self):
        """Actions after upload"""

    def create_meta(self, **args):
        """Deals with creating any meta information"""

    def gui_methods(self, datadir):
        pass

    def property_alignment_expose(self):
        pass

