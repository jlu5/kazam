#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       x11.py
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

from Xlib.display import Display
from gettext import gettext as _

class ScreenInfo(object):
    
    """Contains information about a screen"""
    
    def __init__(self, x, y, width, height, display):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.display = display
        
def get_screens():
    # The list that will store all of our ScreenInfo's
    screens = []
    default_display = Display()
    xinerama_screens = default_display.xinerama_query_screens().screens
    xinerama_screens.reverse()
    # See if we have more than one screen
    dual_monitor = len(xinerama_screens) > 1
    if dual_monitor:
        # For every screen, create a ScreenInfo object with the x,y
        # width, height and the parent display name (i.e. :0.0)
        for screen in xinerama_screens:
            screen_info = ScreenInfo(screen["x"], screen["y"], 
                                    screen["width"], screen["height"], 
                                    default_display.get_display_name())
            screens.append(screen_info)
    # For setups with only one screen, this becomes the 'Screen' option
    # For setups with more than one screen, this becomes the 'All Screens' options
    screen = default_display.screen()
    screen_info = ScreenInfo(0, 0, screen["width_in_pixels"], 
                            screen["height_in_pixels"], 
                            default_display.get_display_name())
    screens.append(screen_info)
    return screens

