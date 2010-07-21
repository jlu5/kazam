#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       export_backend.py
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

class ExportBackend(gobject.GObject):
    
    __gsignals__ = {
    "export-completed"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ([str]),)
    }
    
    def __init__(self, frontend):
        super(ExportBackend, self).__init__()
        
        self.frontend = frontend
        self.frontend.connect("export-requested", self.cb_export_requested)
        
    def cb_export_requested(self, frontend, export_class):
        export_object = export_class()
        export_object.connect("upload-completed", self.cb_upload_complete)
        if export_object.authentication == True:
            if not export_object.authenticate(email, password):
                print "Didn't work"
                return False
            
        export_object.create_meta(**frontend.get_meta())
        export_object.upload(frontend.get_path())
        
    def cb_upload_complete(self, export_class, url):
        self.emit("export-completed", url)
        
