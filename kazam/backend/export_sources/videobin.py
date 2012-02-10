# -*- coding: utf-8 -*-
#
#       videobin.py
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

import pycurl
import os

from kazam.backend.export_sources import UploadSuperSource
#from kazam.frontend.widgets.comboboxes import EasyTextComboBox
# from kazam.utils import setup_ui

class UploadSource(UploadSuperSource):

    URL = "http://www.videobin.org/add"

    ICONS = ("user-trash", "user-trash")
    NAME = "VideoBin"
    REGISTER_URL = None

    META = {
            "title":"entry_title",
            "description":"textview_description",
            "email":"entry_email",
            }

    # FIXME: (eventually) These should be OGV options, however
    # Theora  messes up the frame rate :(
    FFMPEG_OPTIONS = []
    FFMPEG_FILE_EXTENSION = "changed.mp4"

    def __init__(self):
        super(UploadSource, self).__init__()
        self.authentication = False
    ###

    def login_pre(self, username, password):
        pass

    def login_in(self):
        pass

    def login_post(self):
        pass

    ###
    def create_meta(self, **args):
        self.video_entry = args

    def upload_pre(self):
        self.curl = pycurl.Curl()
        self.curl.setopt(self.curl.URL, self.URL)
        self.curl.setopt(self.curl.POST, 1)
        self.curl.setopt(self.curl.WRITEFUNCTION, self._store)

    def upload_in(self, path):
        opts = [("api", "1")]
        for key in ("email", "title", "description"):
            if self.video_entry[key]:
                opts.append((key, self.video_entry[key]))
        opts.append(("videoFile", (self.curl.FORM_FILE, path)))
        self.curl.setopt(self.curl.HTTPPOST, opts)
        self.curl.perform()

    def upload_post(self):
        return self.url

    ###

    def _store(self, buf):
        self.url = buf


    def gui_extra(self, datadir):
        setup_ui(self, os.path.join(datadir, "ui", "export_sources", "videobin.ui"))
