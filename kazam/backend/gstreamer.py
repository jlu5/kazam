# -*- coding: utf-8 -*-
#
#       gstreamer.py
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

import os
import logging
logger = logging.getLogger("GStreamer")

import tempfile
import multiprocessing

#
# This needs to be set before we load GStreamer modules!
#
os.environ["GST_DEBUG_DUMP_DOT_DIR"] = "/tmp"
os.putenv("GST_DEBUG_DUMP_DOT_DIR", "/tmp")

import pygst
pygst.require("0.10")
import gst

from gi.repository import GObject

from subprocess import Popen
from kazam.backend.constants import *
from kazam.utils import *


class Screencast(GObject.GObject):
    __gsignals__ = {
        "flush-done" : (GObject.SIGNAL_RUN_LAST,
                        None,
                        (),
            ),
        }
    def __init__(self, debug):
        GObject.GObject.__init__(self)
        self.tempfile = tempfile.mktemp(prefix="kazam_", suffix=".movie")
        self.muxer_tempfile = "{0}.mux".format(self.tempfile)
        self.pipeline = gst.Pipeline("Kazam")
        self.debug = debug

    def setup_sources(self,
                      video_source,
                      audio_source,
                      audio2_source,
                      codec,
                      capture_cursor,
                      framerate,
                      region,
                      test,
                      dist):


        self.codec = codec
        # Get the number of cores available then use all except one for encoding
        self.cores = multiprocessing.cpu_count()

        if self.cores > 1:
            self.cores -= 1

        self.audio_source = audio_source
        self.audio2_source = audio2_source
        self.video_source = video_source
        self.capture_cursor = capture_cursor
        self.framerate = framerate
        self.region = region
        self.test = test
        self.dist = dist

        logger.debug("Capture Cursor: {0}".format(capture_cursor))
        logger.debug("Framerate : {0}".format(capture_cursor))
        logger.debug("Codec: {0}".format(get_codec_name(codec)))

        if self.video_source:
            self.setup_video_source()

        if self.audio_source:
            self.setup_audio_source()

        if self.audio2_source:
            self.setup_audio2_source()

        self.setup_filesink()
        self.setup_pipeline()

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)

    def setup_video_source(self):

        if self.test:
            self.videosrc = gst.element_factory_make("videotestsrc", "video_src")
            self.videosrc.set_property("pattern", "smpte")
        else:
            self.videosrc = gst.element_factory_make("ximagesrc", "video_src")

        if self.region:
            startx = self.region[0] if self.region[0] > 0 else 0
            starty = self.region[1] if self.region[1] > 0 else 0
            endx = self.region[2]
            endy = self.region[3]
        else:
            startx = self.video_source['x']
            starty = self.video_source['y']
            width = self.video_source['width']
            height = self.video_source['height']
            endx = startx + width - 1
            endy = starty + height - 1


        #
        # H264 requirement is that video dimensions are divisible by 2.
        # If they are not, we have to get rid of that extra pixel.
        #
        if not abs(startx - endx) % 2 and self.codec == CODEC_H264:
            endx -= 1

        if not abs(starty - endy) % 2 and self.codec == CODEC_H264:
            endy -= 1

        logger.debug("Coordinates: {0} {1} {2} {3}".format(startx, starty, endx, endy))

        if self.test:
            logger.info("Using test signal instead of screen capture.")
            self.vid_caps = gst.Caps("video/x-raw-rgb, framerate={0}/1, width={1}, height={2}".format(
                  self.framerate,
                  endx - startx,
                  endy - starty))
            self.vid_caps_filter = gst.element_factory_make("capsfilter", "vid_filter")
            self.vid_caps_filter.set_property("caps", self.vid_caps)
        else:
            self.videosrc.set_property("startx", startx)
            self.videosrc.set_property("starty", starty)
            self.videosrc.set_property("endx", endx)
            self.videosrc.set_property("endy", endy)
            self.videosrc.set_property("use-damage", False)
            self.videosrc.set_property("show-pointer", self.capture_cursor)

            self.vid_caps = gst.Caps("video/x-raw-rgb, framerate={0}/1".format(self.framerate))
            self.vid_caps_filter = gst.element_factory_make("capsfilter", "vid_filter")
            self.vid_caps_filter.set_property("caps", self.vid_caps)

        self.ffmpegcolor = gst.element_factory_make("ffmpegcolorspace", "ffmpeg")
        self.videorate = gst.element_factory_make("videorate", "video_rate")

        if self.codec == CODEC_VP8:
            logger.debug("Codec: VP8/WEBM")
            self.videnc = gst.element_factory_make("vp8enc", "video_encoder")

            if self.dist[0] == 'Ubuntu':
                self.videnc.set_property("speed", 6)
            elif self.dist[0] == 'LinuxMint':
                self.videnc.set_property("speed", 2)

            self.videnc.set_property("max-latency", 1)
            self.videnc.set_property("quality", 8)
            self.videnc.set_property("threads", self.cores)
            self.mux = gst.element_factory_make("webmmux", "muxer")
        elif self.codec == CODEC_H264:
            logger.debug("Codec: H264/MP4")
            self.videnc = gst.element_factory_make("x264enc", "video_encoder")
            self.videnc.set_property("speed-preset", "veryfast")
            self.videnc.set_property("pass", 4)
            self.videnc.set_property("quantizer", 15)
            self.videnc.set_property("threads", self.cores)
            self.mux = gst.element_factory_make("mp4mux", "muxer")
            self.mux.set_property("faststart", 1)
            self.mux.set_property("faststart-file", self.muxer_tempfile)
            self.mux.set_property("streamable", 1)

        self.vid_in_queue = gst.element_factory_make("queue", "queue_v1")
        self.vid_out_queue = gst.element_factory_make("queue", "queue_v2")

    def setup_audio_source(self):
        logger.debug("Audio1 Source:\n  {0}".format(self.audio_source))
        self.audiosrc = gst.element_factory_make("pulsesrc", "audio_src")
        self.audiosrc.set_property("device", self.audio_source)
        self.aud_caps = gst.Caps("audio/x-raw-int")
        self.aud_caps_filter = gst.element_factory_make("capsfilter", "aud_filter")
        self.aud_caps_filter.set_property("caps", self.aud_caps)
        self.audioconv = gst.element_factory_make("audioconvert", "audio_conv")
        if self.codec == CODEC_VP8:
            self.audioenc = gst.element_factory_make("vorbisenc", "audio_encoder")
            self.audioenc.set_property("quality", 1)
        elif self.codec == CODEC_H264:
            self.audioenc = gst.element_factory_make("lamemp3enc", "audio_encoder")
            self.audioenc.set_property("quality", 0)

        self.aud_in_queue = gst.element_factory_make("queue", "queue_a_in")
        self.aud_out_queue = gst.element_factory_make("queue", "queue_a_out")

    def setup_audio2_source(self):
        logger.debug("Audio2 Source:\n  {0}".format(self.audio2_source))
        self.audiomixer = gst.element_factory_make("adder", "audiomixer")
        self.audio2src = gst.element_factory_make("pulsesrc", "audio2_src")
        self.audio2src.set_property("device", self.audio2_source)
        self.aud2_caps = gst.Caps("audio/x-raw-int")
        self.aud2_caps_filter = gst.element_factory_make("capsfilter", "aud2_filter")
        self.aud2_caps_filter.set_property("caps", self.aud2_caps)
        self.audio2conv = gst.element_factory_make("audioconvert", "audio2_conv")

        self.aud2_in_queue = gst.element_factory_make("queue", "queue_a2_in")

    def setup_filesink(self):
        logger.debug("Filesink: {0}".format(self.tempfile))
        self.sink = gst.element_factory_make("filesink", "sink")
        self.sink.set_property("location", self.tempfile)
        self.file_queue = gst.element_factory_make("queue", "queue_file")

    def setup_pipeline(self):
        if self.video_source and not self.audio_source and not self.audio2_source:
            logger.debug("Pipline - Video only".format(self.audio_source))
            self.pipeline.add(self.videosrc, self.vid_in_queue, self.videorate,
                              self.vid_caps_filter, self.ffmpegcolor,
                              self.videnc, self.vid_out_queue, self.mux,
                              self.sink)
            gst.element_link_many(self.videosrc, self.vid_in_queue,
                                  self.videorate, self.vid_caps_filter,
                                  self.ffmpegcolor, self.videnc,
                                  self.vid_out_queue, self.mux,
                                  self.sink)

        elif self.video_source and self.audio_source and not self.audio2_source:
            logger.debug("Pipline - Video + Audio".format(self.audio_source))
            self.pipeline.add(self.videosrc, self.vid_in_queue, self.videorate,
                              self.vid_caps_filter, self.ffmpegcolor,
                              self.videnc, self.audiosrc, self.aud_in_queue,
                              self.aud_caps_filter, self.vid_out_queue,
                              self.aud_out_queue, self.audioconv,
                              self.audioenc, self.mux, self.file_queue, self.sink)

            gst.element_link_many(self.videosrc, self.vid_in_queue,
                                  self.videorate, self.vid_caps_filter,
                                  self.ffmpegcolor, self.videnc,
                                  self.vid_out_queue, self.mux)

            gst.element_link_many(self.audiosrc, self.aud_in_queue,
                                  self.aud_caps_filter,
                                  self.audioconv, self.audioenc,
                                  self.aud_out_queue, self.mux)

            gst.element_link_many(self.mux, self.file_queue, self.sink)

        elif self.video_source and self.audio_source and self.audio2_source:
            logger.debug("Pipline - Video + Dual Audio".format(self.audio_source))
            self.pipeline.add(self.videosrc, self.vid_in_queue, self.videorate,
                              self.vid_caps_filter, self.ffmpegcolor, self.videnc,
                              self.audiosrc, self.aud_in_queue,
                              self.aud_caps_filter, self.vid_out_queue,
                              self.aud_out_queue, self.audioconv,
                              self.audioenc, self.audiomixer, self.aud2_in_queue,
                              self.audio2src, self.aud2_caps_filter,
                              self.mux, self.file_queue, self.sink)

            gst.element_link_many(self.videosrc, self.vid_in_queue,
                                  self.videorate, self.vid_caps_filter,
                                  self.ffmpegcolor, self.videnc,
                                  self.vid_out_queue, self.mux)

            gst.element_link_many(self.audiosrc, self.aud_in_queue,
                                  self.aud_caps_filter, self.audiomixer)

            gst.element_link_many(self.audio2src, self.aud2_in_queue,
                                  self.aud2_caps_filter, self.audiomixer)

            gst.element_link_many(self.audiomixer, self.audioconv,
                                  self.audioenc, self.aud_out_queue, self.mux)

            gst.element_link_many(self.mux, self.file_queue, self.sink)

    def start_recording(self):
        if self.debug:
            logger.debug("Generating dot file.")
            gst.DEBUG_BIN_TO_DOT_FILE(self.pipeline,
                                      gst.DEBUG_GRAPH_SHOW_MEDIA_TYPE |
                                      gst.DEBUG_GRAPH_SHOW_NON_DEFAULT_PARAMS |
                                      gst.DEBUG_GRAPH_SHOW_STATES,
                                      "kazam_debug")


        logger.debug("Setting STATE_PLAYING")
        self.pipeline.set_state(gst.STATE_PLAYING)

    def pause_recording(self):
        logger.debug("Setting STATE_PAUSED")
        self.pipeline.set_state(gst.STATE_PAUSED)

    def unpause_recording(self):
        logger.debug("Setting STATE_PLAYING - UNPAUSE")
        self.pipeline.set_state(gst.STATE_PLAYING)

    def stop_recording(self):
        logger.debug("Sending new EOS event")
        self.pipeline.send_event(gst.event_new_eos())
        #
        # TODO: Improve this ;)
        #
        if self.debug:
            logger.debug("Generating PNG file from DOT file.")
            if os.path.isfile("/usr/bin/dot"):
                os.system("/usr/bin/dot" + " -Tpng -o " + "/tmp/kazam_pipeline.png" + " " + "/tmp/kazam_debug.dot")
            elif os.path.isfile("/usr/local/bin/dot"):
                os.system("/usr/local/bin/dot" + " -Tpng -o " + "/tmp/kazam_pipeline.png" + " " + "/tmp/kazam_debug.dot")
            else:
                logger.debug("Program 'dot' not found. Unable to generate PNG.")

    def get_tempfile(self):
        return self.tempfile

    def get_audio_recorded(self):
        return self.audio

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            logger.debug("Received EOS, setting pipeline to NULL.")
            self.pipeline.set_state(gst.STATE_NULL)
            logger.debug("Emitting flush-done.")
            self.emit("flush-done")
        elif t == gst.MESSAGE_ERROR:
            logger.debug("Received an error message.")
