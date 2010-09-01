#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       recording.py
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

from subprocess import Popen
import tempfile
import os
import gobject
import glib

class Recording(object):
    def __init__(self, audio=False):
        
        self.tempfile = tempfile.mktemp(suffix=".mkv")
        
        # This is horrible :( TODO: use gstreamer pipeline (see below for start)
        args_list = ["ffmpeg", "-f", "x11grab", "-r", "30", "-s", "1024x768", "-i", ":0.0", "-vcodec", "libx264", "-vpre", "lossless_ultrafast", "-threads", "0", self.tempfile ]
        
        if audio:
            args_list = ["ffmpeg", "-f", "alsa", "-ac", "2", "-i", "pulse", "-acodec", "vorbis", "-f", "x11grab", "-r", "30", "-s", "1024x768", "-i", ":0.0", "-vcodec", "libx264", "-vpre", "lossless_ultrafast", "-threads", "0", self.tempfile ]
        
        self.command = Popen(args_list)
    
    def get_filename(self):
        return self.tempfile
    
    def stop(self):
        self.command.kill()
        
        
class Convert(object):
    def __init__(self, file_, options, file_extension):
        self.file_ = file_
        self.options = options
        self.file_extension = file_extension
        
    def convert(self):
        args_list = ["ffmpeg", "-i"]
        
        args_list += [self.file_]
        args_list += self.options
        args_list += [self.file_.split(".")[0]+self.file_extension]
        
        command = Popen(args_list)
        glib.timeout_add(100, self._poll, command)
        
    def _poll(self, command):
        ret = command.poll()
        if ret is None:
            # Keep monitoring
            return True
        else:
            self.converted_file = self.file_.split(".")[0]+self.file_extension
            return False
        
    
        
"""self.pipeline_string = ""
self.add_element("pulsesrc")
self.add_element("audioconvert")
self.add_element("flacenc")
self.add_element("matroskamux", {"name":"mux"})
self.add_element("filesink", {"location":"/tmp/file.mkv"}, endpipe=False)
self.add_element("ximagesrc", {"startx":20, "starty":20, "endx":300, "endy":300})
self.add_element("video/x-raw-rgb,framerate=5/1")
self.add_element("ffmpegcolorspace")
self.add_element("diracenc", {"lossless":"true"})
self.add_element("mux.", endpipe=False)

print self.pipeline_string
self.pipeline = gst.parse_launch(self.pipeline_string)

def add_element(self, element, properties={}, endpipe=True):
self.pipeline_string += element
for prop in properties:
    self.pipeline_string += " %s=%s" % (prop, properties[prop])
if endpipe:
    self.pipeline_string += " ! "
else:
    self.pipeline_string += "  " """