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

from upload_source import UploadSource

class UploadSource(UploadSuperSource):
    
    URL = "http://www.videobin.org/add"
    
    ICONS = ("user-trash", "user-trash")
    NAME = "VideoBin"

    META = {
            "title":"entry_title",
            "description":"textview_description",
            "writeable":"combobox_writeable",
            }
    
    def __init__(self):
        self.authentication = False
        super(VideoBin, self).__init__()

    def upload(self, path):
        c = pycurl.Curl()
        c.setopt(c.URL, self.URL)
        c.setopt(c.POST, 1)
        c.setopt(c.HTTPPOST, [("api", "1"), ("videoFile", (c.FORM_FILE, path))])
        c.setopt(c.WRITEFUNCTION, self.store)
        c.perform()
        self.emit("upload-completed", self.url)
        
    def store(self, buf):
        self.url = buf
    
    def create_meta(self, **args):
        pass

def extra_gui(self, videobin_class, alignment):
    pass
