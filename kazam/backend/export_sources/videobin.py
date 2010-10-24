#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       videobin.py
#       
#       Copyright 2010 Andrew <andrew@karmic-desktop>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
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

import gobject
import pycurl
import os
import gtk

from kazam.backend.export_sources import UploadSuperSource
from kazam.frontend.widgets.comboboxes import EasyTextComboBox
from kazam.utils import setup_ui

class UploadSource(UploadSuperSource):
    
    URL = "http://www.videobin.org/add"
    
    ICONS = ("user-trash", "user-trash")
    NAME = "VideoBin"
    REGISTER_URL = None

    META = {}
    
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
    
    def upload_pre(self):
        self.curl = pycurl.Curl()
        self.curl.setopt(self.curl.URL, self.URL)
        self.curl.setopt(self.curl.POST, 1)
        self.curl.setopt(self.curl.WRITEFUNCTION, self._store)
        
    def upload_in(self, path):
        self.curl.setopt(self.curl.HTTPPOST, [("api", "1"), 
                        ("videoFile", (self.curl.FORM_FILE, path))])
        self.curl.perform()
        
    def upload_post(self):
        return self.url

    ###
        
    def _store(self, buf):
        self.url = buf
        

    def gui_extra(self, datadir):
        setup_ui(self, os.path.join(datadir, "ui", "export_sources", "videobin.ui"))
