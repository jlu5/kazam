# -*- coding: utf-8 -*-
#
#       export_backend.py
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

from gi.repository import GObject

import kazam.backend.export_sources
from kazam.utils import *

class ExportBackend(GObject.GObject):

    __gsignals__ = {
    "authenticate-requested"     : (GObject.SIGNAL_RUN_LAST,
                           GObject.TYPE_NONE,
                           ([GObject.TYPE_PYOBJECT,
                                GObject.TYPE_PYOBJECT,
                                GObject.TYPE_PYOBJECT]),),
    "login-started"     : (GObject.SIGNAL_RUN_LAST,
                           GObject.TYPE_NONE,
                           ( ),),
    "login-completed"     : (GObject.SIGNAL_RUN_LAST,
                           GObject.TYPE_NONE,
                           ([bool]),),
    "convert-started"     : (GObject.SIGNAL_RUN_LAST,
                           GObject.TYPE_NONE,
                           ( ),),
    "convert-completed"     : (GObject.SIGNAL_RUN_LAST,
                           GObject.TYPE_NONE,
                           ([bool]),),
    "upload-started"     : (GObject.SIGNAL_RUN_LAST,
                           GObject.TYPE_NONE,
                           ( ),),
    "upload-completed"     : (GObject.SIGNAL_RUN_LAST,
                           GObject.TYPE_NONE,
                           ([bool, str]),),
    }

    def __init__(self, frontend, datadir):
        super(ExportBackend, self).__init__()

        self.frontend = frontend
        self.frontend.connect("export-requested", self.cb_export_requested)

        self.datadir = datadir
        self.active_export_object = None

        self.error = False

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
        self.error = False
        self.login()
        if not self.error:
            self.create_meta()
        if not self.error:
            self.convert()
        if not self.error:
            self.upload()

    def login(self):
        if self.active_export_object.authentication == True:
            self.emit("authenticate-requested",
                        self.active_export_object.ICONS,
                        self.active_export_object.NAME,
                        self.active_export_object.REGISTER_URL)
        else:
            self.details = (None, None)
        if hasattr(self, "details"):
            try:
                self.emit("login-started")
                (username, password) = self.details
                self.active_export_object.login_pre(username, password)
                create_wait_thread(self.active_export_object.login_in)
                self.active_export_object.login_post()
                success = True
            except Exception, e:
                print e
                self.error = True
                success = False
        else:
            success = False
            self.error = True
        self.emit("login-completed", success)

    def create_meta(self):
        self.active_export_object.create_meta(**self.frontend.get_meta())

    def convert(self):
        self.emit("convert-started")
        try:
            screencast = self.frontend.get_screencast()
            screencast.convert(self.active_export_object.FFMPEG_OPTIONS,
                    self.active_export_object.FFMPEG_FILE_EXTENSION,
                    self.frontend.get_video_quality(),
                    self.frontend.get_audio_quality())
            while not hasattr(screencast, "converted_file"):
                gtk.main_iteration()
            self.converted_file_path = screencast.converted_file
            self.emit("convert-completed", True)
        except Exception, e:
            print e
            self.error = True
            self.emit("convert-completed", False)

    def upload(self):
        self.emit("upload-started")
        url = ""
        try:
            self.active_export_object.upload_pre()
            create_wait_thread(self.active_export_object.upload_in, (self.converted_file_path,))
            url = self.active_export_object.upload_post()
            success = True
        except Exception, e:
            print e
            self.error = True
            success = False
        self.emit("upload-completed", success, url)
