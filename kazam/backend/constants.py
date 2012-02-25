# -*- coding: utf-8 -*-
#
#       constants.py
#
#       Copyright 2012 David Klasinc <bigwhale@lubica.net>
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


# Codecs

CODEC_VP8 = 0
CODEC_H264 = 1


# PulseAudio Error Codes
PA_LOAD_ERROR = 1
PA_GET_STATE_ERROR = 2
PA_STARTUP_ERROR = 3
PA_UNABLE_TO_CONNECT = 4
PA_UNABLE_TO_CONNECT2 = 5
PA_MAINLOOP_START_ERROR = 6
PA_GET_SOURCES_ERROR = 7
PA_GET_SOURCES_TIMEOUT = 8
PA_GET_SOURCE_ERROR = 9
PA_GET_SOURCE_TIMEOUT = 10
PA_MAINLOOP_END_ERROR = 11


# PulseAudio Status Codes
PA_STOPPED = 0
PA_WORKING = 1
PA_FINISHED = 2
PA_ERROR = 3

# PulseAudio State Codes
PA_STATE_READY = 0
PA_STATE_BUSY = 1
PA_STATE_FAILED = 2
PA_STATE_WORKING = 3


# Various actions
ACTION_SAVE = 0
ACTION_EDIT = 1

# Blink modes and states
BLINK_STOP = 0
BLINK_START = 1
BLINK_SLOW = 2
BLINK_FAST = 3
BLINK_STOP_ICON = 4
BLINK_READY_ICON = 5
