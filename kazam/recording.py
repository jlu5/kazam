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

class Recording(object):
    def __init__(self, audio=False):
        
        # This is horrible :( TODO: use gstreamer pipeline
        args_list = ["ffmpeg", "-f", "x11grab", "-r", "30", "-s", "1024x768", "-i", ":0.0", "-vcodec", "libx264", "-vpre", "lossless_ultrafast", "-threads", "0", "/tmp/file.mkv" ]
        
        if audio:
            args_list = ["ffmpeg", "-f", "alsa", "-ac", "2", "-i", "pulse", "-acodec", "pcm_s16le", "-f", "x11grab", "-r", "30", "-s", "1024x768", "-i", ":0.0", "-vcodec", "libx264", "-vpre", "lossless_ultrafast", "-threads", "0", "/tmp/file.mkv" ]
        
        self.command = Popen(args_list)
    
    def stop(self):
        self.command.kill()
