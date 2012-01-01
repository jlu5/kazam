#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       error_handling.py
#       
#       Copyright 2010 David Klasinc <bigwhale@lubica.net>
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

# Error Codes
PA_LOAD_ERROR = 1
PA_GET_STATE_ERROR = 2
PA_STARTUP_ERROR = 3
PA_UNABLE_TO_CONNECT = 4
PA_UNABLE_TO_CONNECT = 5
PA_MAINLOOP_START_ERROR = 6
PA_GET_SOURCES_ERROR = 7
PA_GET_SOURCES_TIMEOUT = 8

# Status Codes
PA_STOPPED = 0
PA_WORKING = 1
PA_FINISHED = 2
PA_ERORO = 3


class PAError(Exception):
    """Used for reporting various Pulse Audio Errors"""
    def __init__(self, value, msg):
        self.value = value
        self.msg = msg

