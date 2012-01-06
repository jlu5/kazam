# -*- coding: utf-8 -*-
#
#       app.py
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

import locale
import gettext
import logging
import os
import shutil
import time

from gettext import gettext as _

from gi.repository import Gtk

from kazam.frontend.indicator import KazamIndicator
from kazam.frontend.window_countdown import CountdownWindow
from kazam.pulseaudio.pulseaudio import pulseaudio_q
from kazam.backend.x11 import get_screens
from kazam.backend.config import KazamConfig

class KazamApp(Gtk.Window):

    def __init__(self, datadir):
        Gtk.Window.__init__(self, title="Kazam Screencaster")

        self.datadir = datadir
        self.setup_translations()

        # Setup config
        self.config = KazamConfig()

        self.connect("delete-event", self.cb_delete_event)

        self.indicator = KazamIndicator()
        self.indicator.connect("quit-requested", self.cb_quit_requested)
        self.indicator.connect("show-requested", self.cb_show_requested)

        self.countdown = CountdownWindow(2)
        self.countdown.connect("record-requested", self.cb_record_requested)

        self.set_border_width(10)

        self.vbox = Gtk.Box(spacing = 20, orientation = Gtk.Orientation.VERTICAL)
        self.grid = Gtk.Grid(row_spacing = 10, column_spacing = 5)
        self.checkbutton_video = Gtk.CheckButton(label=_("Video Source"))
        self.checkbutton_video.connect("toggled", self.cb_video_toggled)
        self.combobox_video = Gtk.ComboBoxText()
        self.grid.add(self.checkbutton_video)
        self.grid.attach_next_to(self.combobox_video,
                                self.checkbutton_video,
                                Gtk.PositionType.RIGHT,
                                1, 1)
        self.checkbutton_audio = Gtk.CheckButton(label=_("Audio Source 1"))
        self.checkbutton_audio.connect("toggled", self.cb_audio_toggled)
        self.combobox_audio = Gtk.ComboBoxText()
        self.grid.attach_next_to(self.checkbutton_audio,
                                 self.checkbutton_video,
                                 Gtk.PositionType.BOTTOM,
                                 1, 1)
        self.grid.attach_next_to(self.combobox_audio,
                                self.checkbutton_audio,
                                Gtk.PositionType.RIGHT,
                                1, 1)
        self.checkbutton_audio2 = Gtk.CheckButton(label=_("Audio Source 2"))
        self.checkbutton_audio2.connect("toggled", self.cb_audio2_toggled)
        self.combobox_audio2 = Gtk.ComboBoxText()
        self.grid.attach_next_to(self.checkbutton_audio2,
                                 self.checkbutton_audio,
                                 Gtk.PositionType.BOTTOM,
                                 1, 1)
        self.grid.attach_next_to(self.combobox_audio2,
                                self.checkbutton_audio2,
                                Gtk.PositionType.RIGHT,
                                1, 1)
        self.label_codec = Gtk.Label(_("Encoder type"))
        self.label_codec.set_justify(Gtk.Justification.RIGHT)
        self.combobox_codec = Gtk.ComboBoxText()
        self.grid.attach_next_to(self.label_codec,
                                 self.checkbutton_audio2,
                                 Gtk.PositionType.BOTTOM,
                                 1, 1)
        self.grid.attach_next_to(self.combobox_codec,
                                self.label_codec,
                                Gtk.PositionType.RIGHT,
                                1, 1)
        self.label_counter = Gtk.Label(_("Countdown timer"))
        self.label_counter.set_justify(Gtk.Justification.RIGHT)
        self.spin_adjustment = Gtk.Adjustment(5, 0, 60, 1, 5, 0)
        self.spinbutton_counter = Gtk.SpinButton()
        self.spinbutton_counter.set_adjustment(self.spin_adjustment)
        self.spinbutton_counter.set_size_request(100, -1)
        self.grid.attach_next_to(self.label_counter,
                                 self.label_codec,
                                 Gtk.PositionType.BOTTOM,
                                 1, 1)
        self.grid.attach_next_to(self.spinbutton_counter,
                                self.label_counter,
                                Gtk.PositionType.RIGHT,
                                1, 1)

        self.combobox_audio.connect("changed", self.cb_audio_changed)
        self.combobox_audio2.connect("changed", self.cb_audio_changed)
        self.btn_record = Gtk.Button(label = _("Record"))
        self.btn_record.set_size_request(100, -1)
        self.btn_record.connect("clicked", self.cb_record_clicked)
        self.btn_close = Gtk.Button(label = _("Close"))
        self.btn_close.set_size_request(100, -1)
        self.btn_close.connect("clicked", self.cb_close_clicked)

        self.hbox = Gtk.Box(spacing = 10)
        self.left_hbox = Gtk.Box()
        self.right_hbox = Gtk.Box(spacing = 5)
        self.right_hbox.pack_start(self.btn_record, False, True, 0)
        self.right_hbox.pack_start(self.btn_close, False, True, 0)

        self.hbox.pack_start(self.left_hbox, True, True, 0)
        self.hbox.pack_start(self.right_hbox, False, False, 0)

        self.vbox.pack_start(self.grid, True, True, 0)
        self.vbox.pack_start(self.hbox, True, True, 0)
        self.add(self.vbox)

        # Fetch sources info
        self.get_sources()
        self.populate_widgets()
        self.restore_state()

        # Simulated stuff
        self.combobox_codec.append(None, "Gstreamer - VP8/WebM")
        self.combobox_codec.append(None, "GStreamer - H264/Matroska")
        self.combobox_codec.append(None, "Ffmpeg - VP8/WebM")
        self.combobox_codec.append(None, "Ffmpeg - H264/Matroska")
        self.combobox_codec.set_active(0)

    #
    # Callbacks, go down here ...
    #
    def cb_quit_requested(self, indicator):
        self.save_state()
        Gtk.main_quit()

    def cb_show_requested(self, indicator):
        self.show_all()
        self.present()

    def cb_close_clicked(self, indicator):
        self.hide()

    def cb_delete_event(self, one, two):
        return self.hide_on_delete()

    def cb_video_toggled(self, widget):
        if self.checkbutton_video.get_active():
            self.combobox_video.set_sensitive(True)
        else:
            self.combobox_video.set_sensitive(False)

        if self.combobox_video.get_sensitive() or self.combobox_audio.get_sensitive():
            self.btn_record.set_sensitive(True)
        else:
            self.btn_record.set_sensitive(False)

    def cb_audio_toggled(self, widget):
        if self.checkbutton_audio.get_active():
            self.combobox_audio.set_sensitive(True)
            self.checkbutton_audio2.set_sensitive(True)
        else:
            self.combobox_audio.set_sensitive(False)
            self.combobox_audio2.set_sensitive(False)
            self.checkbutton_audio2.set_sensitive(False)
            self.checkbutton_audio2.set_active(False)

        if self.combobox_video.get_sensitive() or self.combobox_audio.get_sensitive() or self.combobox_audio2.get_sensitive():
            self.btn_record.set_sensitive(True)
        else:
            self.btn_record.set_sensitive(False)

    def cb_audio2_toggled(self, widget):
        if self.checkbutton_audio2.get_active():
            self.combobox_audio2.set_sensitive(True)
        else:
            self.combobox_audio2.set_sensitive(False)

        if self.combobox_video.get_sensitive() or self.combobox_audio.get_sensitive() or self.combobox_audio2.get_sensitive():
            self.btn_record.set_sensitive(True)
        else:
            self.btn_record.set_sensitive(False)

    def cb_audio_changed(self, widget):
        v1 = self.combobox_audio.get_active()
        v2 = self.combobox_audio2.get_active()
        if v1 == v2:
            self.checkbutton_audio2.set_active(False)
            self.combobox_audio2.set_sensitive(False)
            if v1 < len(self.audio_sources):
                v2 = v2 + 1
            else:
                v2 = 0
            self.combobox_audio2.set_active(v2)

    def cb_record_clicked(self, widget):
        self.countdown.run()
        self.hide()

    def cb_record_requested(self, widget):
        self.indicator.start_recording()


    #
    # Other somewhat usefull stuff ...
    #

    def setup_translations(self):
        gettext.bindtextdomain("kazam", "/usr/share/locale")
        gettext.textdomain("kazam")
        try:
            locale.setlocale(locale.LC_ALL, "")
        except Exception, e:
            logging.exception("setlocale failed")

    def restore_state(self):
        video_toggled = self.config.getboolean("start_recording", "video_toggled")
        audio_toggled = self.config.getboolean("start_recording", "audio_toggled")
        audio2_toggled = self.config.getboolean("start_recording", "audio2_toggled")

        self.checkbutton_video.set_active(video_toggled)
        self.checkbutton_audio.set_active(audio_toggled)
        self.checkbutton_audio2.set_active(audio2_toggled)

        video_source = self.config.getint("start_recording", "video_source")
        audio_source = self.config.getint("start_recording", "audio_source")
        audio2_source = self.config.getint("start_recording", "audio2_source")

        self.combobox_video.set_active(video_source)
        self.combobox_video.set_sensitive(video_toggled)

        self.combobox_audio.set_active(audio_source)
        self.combobox_audio.set_sensitive(audio_toggled)

        self.combobox_audio2.set_active(audio2_source)
        self.combobox_audio2.set_sensitive(audio2_toggled)

        codec = self.config.getint("start_recording", "codec")
        self.combobox_codec.set_active(codec)

        self.spinbutton_counter.set_value(self.config.getfloat("start_recording", "counter"))

        if len(self.audio_sources) == 1:
            self.combobox_audio2.set_active(self.combobox_audio.get_active())
            self.combobox_audio2.set_sensitive(False)
            self.checkbutton_audio2.set_active(False)
            self.checkbutton_audio2.set_sensitive(False)

        if audio_toggled or audio2_toggled or video_toggled:
            self.btn_record.set_sensitive(True)
        else:
            self.btn_record.set_sensitive(False)

        if audio_toggled:
            self.checkbutton_audio2.set_sensitive(True)
        else:
            self.checkbutton_audio2.set_sensitive(False)
            self.checkbutton_audio2.set_active(False)


    def save_state(self):
        video_toggled = self.checkbutton_video.get_active()
        audio_toggled = self.checkbutton_audio.get_active()
        audio2_toggled = self.checkbutton_audio2.get_active()

        video_source = self.combobox_video.get_active()
        audio_source = self.combobox_audio.get_active()
        audio2_source = self.combobox_audio2.get_active()


        self.config.set("start_recording", "video_source", video_source)
        self.config.set("start_recording", "audio_source", audio_source)
        self.config.set("start_recording", "audio2_source", audio2_source)

        self.config.set("start_recording", "video_toggled", video_toggled)
        self.config.set("start_recording", "audio_toggled", audio_toggled)
        self.config.set("start_recording", "audio2_toggled", audio2_toggled)

        codec = self.combobox_codec.get_active()
        self.config.set("start_recording", "codec", codec)

        counter = int(self.spinbutton_counter.get_value())
        self.config.set("start_recording", "counter", counter)

        self.config.write()

    def get_sources(self):
        try:
            pa_q = pulseaudio_q()
            pa_q.start()
            self.audio_sources = pa_q.get_audio_sources()
            pa_q.end()
        except:
            # Something went wrong, just fallback
            # to no-sound
            self.audio_sources = [[0, 'N/A', 'N/A']]

        try:
            self.screens = get_screens()
        except:
            self.screens = _("Screen")

    def populate_widgets(self):
        #
        # Audio first
        #
        for source in self.audio_sources:
            self.combobox_audio.append(None, source[2])
            self.combobox_audio2.append(None, source[2])

        i = 1
        for s in self.screens:
            if i == len(self.screens):
                dsp_name = _("Combined (%dx%d)" % (s.width, s.height))
            else:
                dsp_name = _("Display %d (%sx%s)"  % (i, s.width, s.height))

            self.combobox_video.append(None, dsp_name)
            i = i + 1

