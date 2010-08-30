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

import kazam.backend.export_sources
from kazam.backend.ffmpeg import Convert
from kazam.utils import *

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
    "convert-started"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),),
    "convert-completed"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ([bool]),),
    "upload-started"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),),
    "upload-completed"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ([bool, str]),),
    }
    
    def __init__(self, frontend, datadir):
        super(ExportBackend, self).__init__()
        
        self.frontend = frontend
        self.frontend.connect("export-requested", self.cb_export_requested)
        
        self.datadir = datadir
        self.active_export_object = None
        
        export_module_files = self._get_export_module_files()
        self.export_objects = self._create_export_objects(export_module_files)
        
    def _get_export_module_files(self):
        """
        Returns a list of export source files
        """
        export_module_list = []
        # For each directory that provides kazam.export_sources
        for path in kazam.backend.export_sources.__path__:
            directory = os.path.abspath(path)
            # List files in that directory
            for f in os.listdir(directory):
                # If the file is a python file append the file to our list
                if f[-3:] == ".py":
                    export_module_list.append(f)
                    
        # Remove __init__.py and any duplicates
        export_module_list.remove("__init__.py")
        export_module_list = remove_list_dups(export_module_list)
                    
        return export_module_list
        
    def _import_export_module(self, name):
        """
        Import an export_source module and return the module
        """
        return getattr(__import__("kazam.backend.export_sources", globals(), 
                                    locals(), [name], -1), name)
        
    def _create_export_objects(self, export_module_files):
        """
        Return a list of export objects
        """
        export_objects = []
        for f in export_module_files:
            f = f[:-3]
            # Find and import the module for each file
            module = self._import_export_module(f)
            # Append an instance of it, to our export_objects list
            upload_source = module.UploadSource()
            upload_source.gui_extra(self.datadir)
            export_objects.append(upload_source)
        return export_objects
        
    def get_export_objects(self):
        return self.export_objects
        
    def set_active_export_object(self, i):
        self.active_export_object = self.export_objects[i]
        return self.active_export_object
        
    def get_active_export_object(self):
        return self.active_export_object
        
    def get_export_meta(self):
        return self.export_object.META
        
    def cb_export_requested(self, frontend):
        self.login()
        self.create_meta()
        self.convert()
        self.upload()

    def login(self):
        if self.active_export_object.authentication == True:
            self.emit("authenticate-requested", 
                        self.active_export_object.ICONS, 
                        self.active_export_object.NAME, 
                        self.active_export_object.REGISTER_URL)
        else:
            self.details = (None, None)
        try:
            self.emit("login-started")
            (email, password) = self.details
            self.active_export_object.login_pre(email, password)
            create_wait_thread(self.active_export_object.login_in)
            self.active_export_object.login_post()
            success = True
        except Exception, e:
            print e
            success = False
        self.emit("login-completed", success)
        
    def create_meta(self):
        self.active_export_object.create_meta(**self.frontend.get_meta())
        
    def convert(self):
        self.emit("convert-started")
        try:
            convert = Convert(self.frontend.get_path(), 
                                self.active_export_object.FFMPEG_OPTIONS,
                                self.active_export_object.FFMPEG_FILE_EXTENSION)
            create_wait_thread(convert.convert())
            success = True
        except Exception, e:
            print e
            success = False
        self.emit("convert-finished", success)
        
        
    def upload(self):
        self.emit("upload-started")
        url = ""
        try:
            self.active_export_object.upload_pre()
            create_wait_thread(self.active_export_object.upload_in, (self.frontend.get_path(),))
            url = self.active_export_object.upload_post()
            success = True
        except Exception, e:
            print e
            success = False
        self.emit("upload-completed", success, url)
