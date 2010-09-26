#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       config.py
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

import os
from ConfigParser import SafeConfigParser
from xdg.BaseDirectory import xdg_config_home

class KazamConfig(SafeConfigParser):
    
    DEFAULTS = [{
                "name":"start_recording",
                "keys":{
                        "video_toggled":True,
                        "video_source":0,
                        "audio_toggled":False,
                        "audio_source":0,
                        },
                }]
    
    CONFIGDIR = os.path.join(xdg_config_home, "kazam")
    CONFIGFILE = os.path.join(CONFIGDIR, "kazam.conf")
    
    def __init__(self):
        SafeConfigParser.__init__(self)
        if not os.path.isdir(self.CONFIGDIR):
            os.makedirs(self.CONFIGDIR)
        if not os.path.isfile(self.CONFIGFILE):
            self.create_default()
            self.write()
        self.read(self.CONFIGFILE)
    
    def create_default(self):
        # For every section
        for section in self.DEFAULTS:
            # Add the section
            self.add_section(section["name"])
            # And add every key in it, with its default value
            for key in section["keys"]:
                value = section["keys"][key]
                self.set(section["name"], key, value)

    
    def set(self, section, option, value):
        # If the section referred to doesn't exist (rare case),
        # then create it
        if not self.has_section(section):
            self.add_section(section)
        SafeConfigParser.set(self, section, option, str(value))
        
    def write(self):
        file_ = open(self.CONFIGFILE, "w")
        SafeConfigParser.write(self, file_)
        file_.close()
    

