#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       gstreamer.py
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
