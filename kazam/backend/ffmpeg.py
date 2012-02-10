#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       recording.py
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

from subprocess import Popen
import tempfile
import os
import gobject
import glib
import signal

class Screencast(object):
    def __init__(self):
        self.tempfile = tempfile.mktemp(prefix="kazam_", suffix=".mkv")

    def setup_sources(self, video_source, audio_source):
        self.audio_source = audio_source
        self.video_source = video_source

        # TODO: use gstreamer instead (see gstreamer.py for start)
        self.args_list = ["ffmpeg"]

        # Add the audio source if selected
        if audio_source:
            self.args_list += ["-f", "alsa", "-i", "pulse"]

        # Add the video source
        if video_source:
            x = video_source.x
            y = video_source.y
            width = video_source.width
            height = video_source.height
            display = video_source.display
            self.args_list += ["-f", "x11grab", "-r", "30", "-s",
                        "%sx%s" % (width, height), "-i",
                        "%s+%s,%s" % (display, x, y)]
        if audio_source:
            self.args_list += ["-ac", "2", "-acodec", "flac", "-ab", "128k"]

        if video_source:
            self.args_list += ["-vcodec", "libx264",
                               "-crf", "0",
                               "-preset", "fast",
                               "-tune", "stillimage",
                               "-vf", "unsharp=3:3:0.5:3:3:0.0"

                              ]
        self.args_list += ["-threads", "0", self.tempfile]

        arg_string = ""
        for arg in self.args_list:
            arg_string += " %s" % arg
        print arg_string

    def start_recording(self):
        self.recording_command = Popen(self.args_list)

    def pause_recording(self):
        self.recording_command.send_signal(signal.SIGTSTP)

    def unpause_recording(self):
        self.recording_command.send_signal(signal.SIGCONT)

    def stop_recording(self):
        self.recording_command.send_signal(signal.SIGINT)

    def get_recording_filename(self):
        return self.tempfile

    def get_audio_recorded(self):
        return self.audio_source

    def get_video_recorded(self):
        return self.video_source

    def convert(self, options, converted_file_extension, video_quality=None,
                    audio_quality=None):

        self.converted_file_extension = converted_file_extension

        # Create our ffmpeg arguments list
        args_list = ["ffmpeg"]
        # Add the input file
        args_list += ["-i", self.tempfile]
        # Add any UploadSource specific options
        args_list += options

        # Configure the quality as selected by the user
        # If the quality slider circle is at the right-most position
        # use the same quality option
        if video_quality == 6001:
            args_list += ["-sameq"]
        elif video_quality:
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

