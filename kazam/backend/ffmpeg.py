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
import signal

class Screencast(object):
    def __init__(self):
        self.tempfile = tempfile.mktemp(suffix=".mkv")
        
    def start_recording(self, video_source, audio=False):
        self.audio = audio
        x = video_source.x
        y = video_source.y
        width = video_source.width
        height = video_source.height
        display = video_source.display
        
        # TODO: use gstreamer instead (see gstreamer.py for start)
        args_list = ["ffmpeg"]
        
        # Add the audio source if selected
        if audio:
            args_list += ["-f", "alsa", "-ac", "2", "-i", "pulse", 
                        "-acodec", "vorbis"]
        
        # Add the video source
        args_list += ["-f", "x11grab", "-r", "30", "-s", 
                    "%sx%s" % (width, height), "-i", 
                    "%s+%s,%s" % (display, x, y), "-vcodec", "libx264", 
                    "-vpre", "lossless_ultrafast", "-threads", "0", 
                    self.tempfile]
        
        self.recording_command = Popen(args_list)
    
    def pause_recording(self):
        self.recording_command.send_signal(signal.SIGTSTP)
        
    def unpause_recording(self):
        self.recording_command.send_signal(signal.SIGCONT)
    
    def stop_recording(self):
        self.recording_command.send_signal(signal.SIGINT)
        
    def get_recording_filename(self):
        return self.tempfile
        
    def get_audio_recorded(self):
        return self.audio
        
    def convert(self, options, converted_file_extension, video_quality,
                    audio_quality=None):
                        
        self.converted_file_extension = converted_file_extension
        
        # Create our ffmpeg arguments list
        args_list = ["ffmpeg"]
        # Add the input file
        args_list += ["-i", self.tempfile]
        # Add any UploadSource specific options
        args_list += options
        # Configure the quality as selected by the user
        args_list += ["-b", "%sk" % video_quality]
        if audio_quality:
            args_list += ["-ab", "%sk" % audio_quality]
        # Finally add the desired output file
        args_list += ["%s%s" %(self.tempfile[:-4], converted_file_extension)]
        
        # Run the ffmpeg command and when it is done, set a variable to 
        # show we have finished
        command = Popen(args_list)
        glib.timeout_add(100, self._poll, command)
        
    def _poll(self, command):
        ret = command.poll()
        if ret is None:
            # Keep monitoring
            return True
        else:
            self.converted_file = "%s%s" %(self.tempfile[:-4], self.converted_file_extension)
            return False
        
