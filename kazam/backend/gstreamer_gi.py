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
logger = logging.getLogger("GStreamer-GI")

import tempfile
import multiprocessing

#
# This needs to be set before we load GStreamer modules!
#
os.environ["GST_DEBUG_DUMP_DOT_DIR"] = "/tmp"
os.putenv("GST_DEBUG_DUMP_DOT_DIR", "/tmp")

from gi.repository import GObject, Gst

from subprocess import Popen
from kazam.backend.constants import *
from kazam.utils import *


GObject.threads_init()
Gst.init(None)

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
        self.pipeline = Gst.Pipeline("Kazam")
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
        logger.debug("Codec: {0}".format(CODEC_LIST[codec][1]))

        if self.video_source:
            self.setup_video_source()

        if self.audio_source:
            self.setup_audio_source()

        if self.audio2_source:
            self.setup_audio2_source()

        self.setup_filesink()
        self.setup_pipeline()
        self.setup_links()

        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect("message", self.on_message)

    def setup_video_source(self):

        if self.test:
            self.videosrc = Gst.ElementFactory.make("videotestsrc", "video_src")
            self.videosrc.set_property("pattern", "smpte")
        else:
            self.videosrc = Gst.ElementFactory.make("ximagesrc", "video_src")

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
            self.vid_caps = Gst.Caps("video/x-raw-rgb, framerate={0}/1, width={1}, height={2}".format(
                  self.framerate,
                  endx - startx,
                  endy - starty))
            self.vid_caps_filter = Gst.ElementFactory.make("capsfilter", "vid_filter")
            self.vid_caps_filter.set_property("caps", self.vid_caps)
        else:
            self.videosrc.set_property("startx", startx)
            self.videosrc.set_property("starty", starty)
            self.videosrc.set_property("endx", endx)
            self.videosrc.set_property("endy", endy)
            self.videosrc.set_property("use-damage", False)
            self.videosrc.set_property("show-pointer", self.capture_cursor)

            self.vid_caps = Gst.Caps("video/x-raw-rgb, framerate={0}/1".format(self.framerate))
            self.vid_caps_filter = Gst.ElementFactory.make("capsfilter", "vid_filter")
            self.vid_caps_filter.set_property("caps", self.vid_caps)

        self.ffmpegcolor = Gst.ElementFactory.make("ffmpegcolorspace", "ffmpeg")
        self.videorate = Gst.ElementFactory.make("videorate", "video_rate")

        logger.debug("Codec: {0}".format(CODEC_LIST[self.codec][2]))

        if self.codec is not CODEC_RAW:
            self.videnc = Gst.ElementFactory.make(CODEC_LIST[self.codec][1], "video_encoder")

        if self.codec == CODEC_RAW:
            self.mux = Gst.ElementFactory.make("avimux", "muxer")
        elif self.codec == CODEC_VP8:
            if self.dist[0] == 'Ubuntu':
                self.videnc.set_property("speed", 6)
            elif self.dist[0] == 'LinuxMint':
                self.videnc.set_property("speed", 2)
            self.videnc.set_property("max-latency", 1)
            self.videnc.set_property("quality", 8)
            self.videnc.set_property("threads", self.cores)
            self.mux = Gst.ElementFactory.make("webmmux", "muxer")
        elif self.codec == CODEC_H264:
            self.videnc.set_property("speed-preset", "veryfast")
            self.videnc.set_property("pass", 4)
            self.videnc.set_property("quantizer", 15)
            self.videnc.set_property("threads", self.cores)
            self.mux = Gst.ElementFactory.make("mp4mux", "muxer")
            self.mux.set_property("faststart", 1)
            self.mux.set_property("faststart-file", self.muxer_tempfile)
            self.mux.set_property("streamable", 1)
        elif self.codec == CODEC_HUFF:
            self.mux = Gst.ElementFactory.make("avimux", "muxer")
            self.videnc.set_property("bitrate", 500000)
        elif self.codec == CODEC_JPEG:
            self.mux = Gst.ElementFactory.make("avimux", "muxer")

        self.vid_in_queue = Gst.ElementFactory.make("queue", "queue_v1")
        self.vid_out_queue = Gst.ElementFactory.make("queue", "queue_v2")

    def setup_audio_source(self):
        logger.debug("Audio1 Source:\n  {0}".format(self.audio_source))
        self.audiosrc = Gst.ElementFactory.make("pulsesrc", "audio_src")
        self.audiosrc.set_property("device", self.audio_source)
        self.aud_caps = Gst.Caps("audio/x-raw-int")
        self.aud_caps_filter = Gst.ElementFactory.make("capsfilter", "aud_filter")
        self.aud_caps_filter.set_property("caps", self.aud_caps)
        self.audioconv = Gst.ElementFactory.make("audioconvert", "audio_conv")
        if self.codec == CODEC_VP8:
            self.audioenc = Gst.ElementFactory.make("vorbisenc", "audio_encoder")
            self.audioenc.set_property("quality", 1)
        else:
            self.audioenc = Gst.ElementFactory.make("lamemp3enc", "audio_encoder")
            self.audioenc.set_property("quality", 0)

        self.aud_in_queue = Gst.ElementFactory.make("queue", "queue_a_in")
        self.aud_out_queue = Gst.ElementFactory.make("queue", "queue_a_out")

    def setup_audio2_source(self):
        logger.debug("Audio2 Source:\n  {0}".format(self.audio2_source))
        self.audiomixer = Gst.ElementFactory.make("adder", "audiomixer")
        self.audio2src = Gst.ElementFactory.make("pulsesrc", "audio2_src")
        self.audio2src.set_property("device", self.audio2_source)
        self.aud2_caps = Gst.Caps("audio/x-raw-int")
        self.aud2_caps_filter = Gst.ElementFactory.make("capsfilter", "aud2_filter")
        self.aud2_caps_filter.set_property("caps", self.aud2_caps)
        self.aud2_in_queue = Gst.ElementFactory.make("queue", "queue_a2_in")

    def setup_filesink(self):
        logger.debug("Filesink: {0}".format(self.tempfile))
        self.sink = Gst.ElementFactory.make("filesink", "sink")
        self.sink.set_property("location", self.tempfile)
        self.file_queue = Gst.ElementFactory.make("queue", "queue_file")

    #
    # One day, this horrific code will be optimised... I promise!
    #
    def setup_pipeline(self):
        #
        # Behold, setup the master pipeline
        #
        self.pipeline.add(self.videosrc)
        self.pipeline.add(self.vid_in_queue)
        self.pipeline.add(self.videorate)
        self.pipeline.add(self.vid_caps_filter)
        self.pipeline.add(self.ffmpegcolor)
        self.pipeline.add(self.vid_out_queue)
        self.pipeline.add(self.file_queue)

        if self.codec is not CODEC_RAW:
            self.pipeline.add(self.videnc)

        if self.audio_source:
            self.pipeline.add(self.audiosrc)
            self.pipeline.add(self.aud_in_queue)
            self.pipeline.add(self.aud_caps_filter)
            self.pipeline.add(self.aud_out_queue)
            self.pipeline.add(self.audioconv)
            self.pipeline.add(self.audioenc)

        if self.audio2_source:
            self.pipeline.add(self.audiomixer)
            self.pipeline.add(self.aud2_in_queue)
            self.pipeline.add(self.audio2src)
            self.pipeline.add(self.aud2_caps_filter)

        self.pipeline.add(self.mux)
        self.pipeline.add(self.sink)
        logger.debug("Linking pipeline for:")

    def setup_links(self):
        # Connect everything together
        self.videosrc.link(self.vid_in_queue)
        self.vid_in_queue.link(self.videorate)
        self.videorate.link(self.vid_caps_filter)
        self.vid_caps_filter.link(self.ffmpegcolor)
        if self.codec is CODEC_RAW:
            self.ffmpegcolor.link(self.vid_out_queue)
            logger.debug("  RAW Video")
        else:
            logger.debug("  Video")
            self.ffmpegcolor.link(self.videnc)
            self.videnc.link(self.vid_out_queue)

        self.vid_out_queue.link(self.mux)

        if self.audio_source:
            logger.debug("  Audio")
            self.audiosrc.link(self.aud_in_queue)
            self.aud_in_queue.link(self.aud_caps_filter)

            if self.audio2_source:
                logger.debug("  Audio2")
                # Link first audio source to mixer
                self.aud_caps_filter.link(self.audiomixer)

                # Link second audio source to mixer
                self.audio2src.link(self.aud2_in_queue)
                self.aud2_in_queue.link(self.aud2_caps_filter)
                self.aud2_caps_filte.link(self.audiomixer)

                # Link mixer to audio convert
                self.audiomixer.link(self.audioconv)
            else:
                # Link first audio source to audio convert
                self.aud_caps_filter.link(self.audioconv)

            # Link audio to muxer
            self.audioconv.link(self.audioenc)
            self.audioenc.link(self.aud_out_queue)
            self.aud_out_queue.link(self.mux)

        self.mux.link(self.file_queue)
        self.file_queue.link(self.sink)

    def start_recording(self):
        if self.debug:
            logger.debug("Generating dot file.")

        logger.debug("Setting STATE_PLAYING")
        self.pipeline.set_state(Gst.State.PLAYING)

    def pause_recording(self):
        logger.debug("Setting STATE_PAUSED")
        self.pipeline.set_state(Gst.State.PAUSED)

    def unpause_recording(self):
        logger.debug("Setting STATE_PLAYING - UNPAUSE")
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop_recording(self):
        logger.debug("Sending new EOS event")
        self.pipeline.send_event(Gst.Event.new_eos())

    def get_tempfile(self):
        return self.tempfile

    def get_audio_recorded(self):
        return self.audio

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            logger.debug("Received EOS, setting pipeline to NULL.")
            self.pipeline.set_state(Gst.State.NULL)
            logger.debug("Emitting flush-done.")
            self.emit("flush-done")
        elif t == Gst.MessageType.ERROR:
            logger.debug("Received an error message.")


def detect_codecs():
    codecs_supported = []
    codec_test = None
    for codec in CODEC_LIST:
        if codec[0]:
            try:
                codec_test = Gst.ElementFactory.make(codec[1], "video_encoder")
            except:
                logger.info("Unable to find {0} GStreamer plugin - support disabled.".format(codec))
                codec_test = None

            if codec_test:
                codecs_supported.append(codec[0])
                logger.info("Supported encoder: {0}.".format(codec[2]))
        else:
            # RAW codec is None, so we don't try to load it.
            codecs_supported.append(codec[0])
            logger.info("Supported encoder: {0}.".format(codec[2]))
        codec_test = None
    return codecs_supported

def get_codec(codec):
    for c in CODEC_LIST:
        if c[0] == codec:
            return c
    return None
