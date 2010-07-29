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
import gtk
import os

import kazam.export_sources
from utils import *

class ExportBackend(gobject.GObject):
    
    __gsignals__ = {
    "authenticate-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ([gobject.TYPE_PYOBJECT, 
                                gobject.TYPE_PYOBJECT, 
                                gobject.TYPE_PYOBJECT]),),
    "login-started"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),),
    "login-completed"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ([bool]),),
    "upload-started"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),),
    "upload-completed"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ([bool, str]),),
    }
    
    def __init__(self, frontend):
        super(ExportBackend, self).__init__()
        
        self.frontend = frontend
        self.frontend.connect("export-requested", self.cb_export_requested)
        
        self.export_object = None
        
    def get_export_meta(self):
        return self.export_object.META
        
    def cb_export_requested(self, frontend, export_class):
        self.export_object = export_class()
        
        self.login()
        self.create_meta()
        self.upload()

    def login(self):
        if self.export_object.authentication == True:
            self.emit("authenticate-requested", 
                        self.export_object.ICONS, 
                        self.export_object.NAME, 
                        self.export_object.REGISTER_URL)
        try:
            self.emit("login-started")
            (email, password) = self.details
            self.export_object.login_pre(email, password)
            create_wait_thread(self.export_object.login_in)
            self.export_object.login_post()
            success = True
        except Exception, e:
            print e
            success = False
        self.emit("login-completed", success)
        
    def create_meta(self):
        self.export_object.create_meta(**self.frontend.get_meta())
        
    def upload(self):
        self.emit("upload-started")
        url = ""     
        try:
            self.export_object.upload_pre()
            create_wait_thread(self.export_object.upload_in, (self.frontend.get_path(),))
            url = self.export_object.upload_post()
            success = True
        except:
            success = False
        self.emit("upload-completed", success, url)
        
    def _get_export_module_files(self):
        export_module_list = []
        export_module_dirs = []
        for path in kazam.export_sources.__path__:
            export_module_dirs.append(os.path.abspath(path))
        for directory in export_module_dirs:
            for f in os.listdir(directory):
                if f.endswith(".py") and f != "__init__.py" and not f in export_module_list:
                    export_module_list.append(f[:-3])
        # REMOVE!!!
        export_module_list.remove("videobin")
                    
        return export_module_list
        
    def get_export_modules(self):
        export_module_list = self._get_export_module_files()
        export_module_dict = {}
        for f in export_module_list:
            export_module = getattr(__import__("kazam.export_sources", globals(), locals(), [f], -1), f)
            name = export_module.UploadSource.NAME
            icon = export_module.UploadSource.ICONS[0]
            export_module_dict[name] = [icon, export_module]
        return export_module_dict
