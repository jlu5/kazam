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

import os
import locale
import gettext
import logging
logger = logging.getLogger("Main")

from subprocess import Popen
from gi.repository import Gtk, Gdk, GObject
from gettext import gettext as _

from kazam.backend.config import KazamConfig
from kazam.frontend.main_menu import MainMenu
from kazam.frontend.about_dialog import AboutDialog
from kazam.frontend.indicator import KazamIndicator
from kazam.pulseaudio.pulseaudio import pulseaudio_q
from kazam.frontend.window_region import RegionWindow
from kazam.frontend.done_recording import DoneRecording
from kazam.frontend.window_countdown import CountdownWindow

class KazamApp(GObject.GObject):

    def __init__(self, datadir, debug):
        GObject.GObject.__init__(self)
        logger.debug("Setting variables.")
        self.datadir = datadir
        self.debug = debug
        self.setup_translations()

        self.icons = Gtk.IconTheme.get_default()
        self.icons.append_search_path(os.path.join(datadir,"icons", "48x48", "apps"))
        self.icons.append_search_path(os.path.join(datadir,"icons", "16x16", "apps"))

        # Initialize all the variables

        self.video_sources = []
        self.video_source = 0
        self.audio_source = 0
        self.audio_source2 = 0
        self.codec = 0
        self.countdown = None
        self.tempfile = ""
        self.recorder = None
        self.capture_cursor = True
        self.region_window = None
        self.region = None
        self.old_path = None

        self.pa_q = pulseaudio_q()
        self.pa_q.start()

        self.mainmenu = MainMenu()

        #
        # Setup config
        #
        self.config = KazamConfig()

        # self.connect("delete-event", self.cb_delete_event)

        logger.debug("Connecting indicator signals.")
        self.indicator = KazamIndicator()
        self.indicator.connect("quit-request", self.cb_quit_request)
        self.indicator.connect("show-request", self.cb_show_request)
        self.indicator.connect("stop-request", self.cb_stop_request)
        self.indicator.connect("pause-request", self.cb_pause_request)
        self.indicator.connect("unpause-request", self.cb_unpause_request)

        self.mainmenu.connect("file-quit", self.cb_quit_request)
        self.mainmenu.connect("help-about", self.cb_help_about)

        #
        # Setup UI
        #
        logger.debug("Main Window UI setup.")

        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(self.datadir, "ui", "kazam.ui"))
        self.builder.connect_signals(self)
        for w in self.builder.get_objects():
            if issubclass(type(w), Gtk.Buildable):
                name = Gtk.Buildable.get_name(w)
                print "GOT:", name
                setattr(self, name, w)
            else:
                logger.debug("Unable to get name for '%s'" % w)

        self.default_screen = Gdk.Screen.get_default()
        self.default_screen.connect("size-changed", self.cb_screen_size_changed)
        # Fetch sources info
        self.get_sources()
        self.populate_widgets()
        self.window.show_all()
        #self.restore_state()

    #
    # Callbacks, go down here ...
    #
    def cb_screen_size_changed(self, screen):
        logger.debug("Screen size changed.")
        old_source = self.video_source
        old_num = len(self.video_sources)
        self.get_sources(audio = False)
        self.populate_widgets(audio = False)
        if old_source > old_num:
            old_source = 0
        self.combobox_video.set_active(old_source)

    def cb_quit_request(self, indicator):
        logger.debug("Quit requested.")
        try:
            os.remove(self.recorder.tempfile)
        except:
            pass

        self.save_state()
        self.pa_q.end()
        Gtk.main_quit()

    def cb_show_request(self, indicator):
        logger.debug("Show requested, raising window.")
        self.show_all()
        self.present()

    def cb_close_clicked(self, indicator):
        self.hide()

    def cb_delete_event(self, widget, user_data):
        return self.hide_on_delete()

    def cb_video_toggled(self, widget):
        logger.debug("Video Toggled.")
        if self.checkbutton_video.get_active():
            self.combobox_video.set_sensitive(True)
        else:
            self.combobox_video.set_sensitive(False)

        if self.combobox_video.get_sensitive():
            self.btn_record.set_sensitive(True)
        else:
            self.btn_record.set_sensitive(False)

    def cb_audio_toggled(self, widget):
        logger.debug("Audio1 Toggled.")
        if self.checkbutton_audio.get_active():
            self.combobox_audio.set_sensitive(True)
            self.checkbutton_audio2.set_sensitive(True)
            self.volumebutton_audio.set_sensitive(True)
        else:
            self.combobox_audio.set_sensitive(False)
            self.volumebutton_audio.set_sensitive(False)
            self.combobox_audio2.set_sensitive(False)
            self.checkbutton_audio2.set_sensitive(False)
            self.checkbutton_audio2.set_active(False)
            self.volumebutton_audio2.set_sensitive(False)

    def cb_audio2_toggled(self, widget):
        logger.debug("Audio2 Toggled.")
        if self.checkbutton_audio2.get_active():
            self.combobox_audio2.set_sensitive(True)
            self.volumebutton_audio2.set_sensitive(True)
        else:
            self.combobox_audio2.set_sensitive(False)
            self.volumebutton_audio2.set_sensitive(False)

    def cb_audio_changed(self, widget):
        logger.debug("Audio Changed.")
        self.audio_source = self.combobox_audio.get_active()
        self.audio2_source  = self.combobox_audio2.get_active()

        logger.debug("  - A_1 {0}".format(self.audio_source))
        logger.debug("  - A_2 {0}".format(self.audio2_source))

        pa_audio_idx =  self.audio_sources[self.audio_source][0]
        pa_audio2_idx =  self.audio_sources[self.audio2_source][0]
        logger.debug("  - PA Audio1 IDX: {0}".format(pa_audio_idx))
        logger.debug("  - PA Audio2 IDX: {0}".format(pa_audio2_idx))
        self.audio_source_info = self.pa_q.get_source_info_by_index(pa_audio_idx)
        self.audio2_source_info = self.pa_q.get_source_info_by_index(pa_audio2_idx)

        if len(self.audio_source_info):
            logger.debug("New Audio1:\n  {0}".format(self.audio_source_info[3]))
        else:
            logger.debug("New Audio1:\n  Error retrieving data.")

        if len(self.audio2_source_info):
            logger.debug("New Audio2:\n  {0}".format(self.audio2_source_info[3]))
        else:
            logger.debug("New Audio2:\n  Error retrieving data.")

        if self.audio_source == self.audio2_source:
            self.checkbutton_audio2.set_active(False)
            self.combobox_audio2.set_sensitive(False)
            if self.audio_source < len(self.audio_sources):
                self.audio2_source += 1
            else:
                self.audio2_source = 0
            self.combobox_audio2.set_active(self.audio2_source)

    def cb_video_changed(self, widget):
        logger.debug("Video changed.")
        self.video_source = self.combobox_video.get_active()
        logger.debug("New Video: {0}".format(self.video_sources[self.video_source]))

    def cb_codec_changed(self, widget):
        logger.debug("Codec changed.")
        self.codec = self.combobox_codec.get_active()

    def cb_record_clicked(self, widget):
        logger.debug("Record clicked, invoking Screencast.")
        from kazam.backend.gstreamer import Screencast

        self.recorder = Screencast(self.debug)

        if self.switch_audio.get_active():
            audio_source = self.audio_sources[self.audio_source][1]
        else:
            audio_source = None

        if self.switch.audio2.get_active():
            audio2_source = self.audio_sources[self.audio2_source][1]
        else:
            audio2_source = None

        if self.switch_button_video.get_active():
            video_source = self.video_sources[self.video_source]
        else:
            video_source = None
        if self.btn_region.get_active():
            region = self.region
        else:
            region = None

        framerate = self.spinbutton_framerate.get_value_as_int()
        self.recorder.setup_sources(video_source,
                                    audio_source,
                                    audio2_source,
                                    self.codec,
                                    self.capture_cursor,
                                    framerate,
                                    region)

        self.recorder.connect("flush-done", self.cb_flush_done)
        self.countdown = CountdownWindow()
        self.countdown.connect("start-request", self.cb_start_request)
        self.countdown.run(self.spinbutton_counter.get_value_as_int())
        logger.debug("Hiding main window.")
        self.hide()

    def cb_volume_changed(self, widget, value):
        logger.debug("Volume 1 changed, new value: {0}".format(value))
        idx = self.combobox_audio.get_active()
        pa_idx =  self.audio_sources[idx][0]
        chn = self.audio_source_info[2].channels
        cvol = self.pa_q.dB_to_cvolume(chn, value-60)
        self.pa_q.set_source_volume_by_index(pa_idx, cvol)

    def cb_volume2_changed(self, widget, value):
        logger.debug("Volume 2 changed, new value: {0}".format(value))
        idx = self.combobox_audio2.get_active()
        pa_idx =  self.audio_sources[idx][0]
        chn = self.audio2_source_info[2].channels
        cvol = self.pa_q.dB_to_cvolume(chn, value-60)
        self.pa_q.set_source_volume_by_index(pa_idx, cvol)

    def cb_start_request(self, widget):
        logger.debug("Start request.")
        self.countdown = None
        self.indicator.start_recording()
        self.recorder.start_recording()

    def cb_stop_request(self, widget):
        logger.debug("Stop request.")
        self.recorder.stop_recording()
        self.tempfile = self.recorder.get_tempfile()
        logger.debug("Recorded tmp file: {0}".format(self.tempfile))
        logger.debug("Waiting for data to flush.")

    def cb_flush_done(self, widget):
        self.done_recording = DoneRecording(self.icons,
                                            self.tempfile,
                                            self.codec,
                                            self.old_path)
        logger.debug("Done Recording initialized.")
        self.done_recording.connect("save-done", self.cb_save_done)
        self.done_recording.connect("save-cancel", self.cb_save_cancel)
        self.done_recording.connect("edit-request", self.cb_edit_request)
        self.done_recording.show_all()
        logger.debug("Signals connected.")
        self.set_sensitive(False)

    def cb_pause_request(self, widget):
        logger.debug("Pause requested.")
        self.recorder.pause_recording()

    def cb_unpause_request(self, widget):
        logger.debug("Unpause requested.")
        self.recorder.unpause_recording()

    def cb_save_done(self, widget, result):
        logger.debug("Save Done, result: {0}".format(result))
        self.old_path = result
        self.window.set_sensitive(True)
        self.window.show_all()
        self.window.present()

    def cb_save_cancel(self, widget):
        try:
            logger.debug("Save canceled, removing {0}".format(self.tempfile))
            os.remove(self.tempfile)
        except:
            logger.info("Failed to remove tempfile {0}".format(self.tempfile))
            pass

        self.window.set_sensitive(True)
        self.window.show_all()
        self.window.present()

    def cb_help_about(self, widget):
        AboutDialog(self.icons)

    def cb_edit_request(self, widget, data):
        (command, arg_list) = data
        arg_list.insert(0, command)
        arg_list.append(self.tempfile)
        logger.debug("Edit request, cmd: {0}".format(arg_list))
        Popen(arg_list)
        self.window.set_sensitive(True)
        self.window.show_all()

    def cb_checkbutton_cursor_toggled(self, widget):
        if self.switch_cursor.get_active():
            logger.debug("Cursor capturing ON.")
            self.capture_cursor = True
        else:
            logger.debug("Cursor capturing OFF.")
            self.capture_cursor = False

    def cb_btn_region_toggled(self, widget):
        logger.debug("Toggle region recording.")
        if self.btn_region.get_active():
            self.region_window = RegionWindow(self.region)
            self.region_window.connect("region-selected", self.cb_region_selected)
            self.region_window.connect("region-canceled", self.cb_region_canceled)
            self.set_sensitive(False)
        else:
            logger.debug("Region cleared.")
            self.region_window.window.destroy()
            self.region_window = None

    def cb_region_selected(self, widget):
        logger.debug("Region selected: {0}, {1}, {2}, {3}".format(
                                                                   self.region_window.startx,
                                                                   self.region_window.starty,
                                                                   self.region_window.endx,
                                                                   self.region_window.endy))
        self.window.set_sensitive(True)
        self.region = (self.region_window.startx,
                       self.region_window.starty,
                       self.region_window.endx,
                       self.region_window.endy)

    def cb_region_canceled(self, widget):
        logger.debug("Region Canceled.")
        self.set_sensitive(True)
        self.btn_region.set_active(False)


    #
    # Other somewhat useful stuff ...
    #

    def setup_translations(self):
        gettext.bindtextdomain("kazam", "/usr/share/locale")
        gettext.textdomain("kazam")
        try:
            locale.setlocale(locale.LC_ALL, "")
        except Exception, e:
            logger.exception("setlocale failed")

    def restore_state(self):
        video_toggled = self.config.getboolean("main", "video_toggled")
        audio_toggled = self.config.getboolean("main", "audio_toggled")
        audio2_toggled = self.config.getboolean("main", "audio2_toggled")

        self.switch_video.set_active(video_toggled)
        self.switch_audio.set_active(audio_toggled)
        self.switch_audio2.set_active(audio2_toggled)

        video_source = self.config.getint("main", "video_source")
        audio_source = self.config.getint("main", "audio_source")
        audio2_source = self.config.getint("main", "audio2_source")
        logger.debug("Restoring state - sources: V ({0}), A_1 ({1}), A_2 ({2})".format(video_source,
                                                                                        audio_source,
                                                                                        audio2_source))
        self.video_source = video_source
        self.audio_source = audio_source
        self.audio2_source = audio2_source

        self.combobox_video.set_active(video_source)
        self.combobox_video.set_sensitive(video_toggled)

        self.combobox_audio.set_active(audio_source)
        self.combobox_audio.set_sensitive(audio_toggled)

        self.combobox_audio2.set_active(audio2_source)
        self.combobox_audio2.set_sensitive(audio2_toggled)

        logger.debug("Getting volume info.")
        pa_audio_idx =  self.audio_sources[self.audio_source][0]
        pa_audio2_idx =  self.audio_sources[self.audio2_source][0]
        audio_info = self.pa_q.get_source_info_by_index(pa_audio_idx)
        audio2_info = self.pa_q.get_source_info_by_index(pa_audio2_idx)

        #
        # TODO: Deal with this in a different way
        #
        if len(audio_info) > 0:
            audio_vol = 60 + self.pa_q.cvolume_to_dB(audio_info[2])
        else:
            logger.debug("Error getting volume info for Audio 1")
            audio_vol = 0
        if len(audio2_info) > 0:
            audio2_vol = 60 + self.pa_q.cvolume_to_dB(audio2_info[2])
        else:
            logger.debug("Error getting volume info for Audio 2")
            audio2_vol = 0

        logger.debug("Restoring state - volume: A_1 ({0}), A_2 ({1})".format(audio_vol,
                                                                               audio2_vol))
        self.volumebutton_audio.set_sensitive(audio_toggled)
        self.volumebutton_audio.set_value(audio_vol)
        self.volumebutton_audio2.set_sensitive(audio2_toggled)
        self.volumebutton_audio2.set_value(audio2_vol)

        codec = self.config.getint("main", "codec")
        self.combobox_codec.set_active(codec)
        self.codec = codec

        self.spinbutton_counter.set_value(self.config.getfloat("main", "counter"))
        self.spinbutton_framerate.set_value(self.config.getfloat("main", "framerate"))

        self.switch_cursor.set_active(self.config.getboolean("main", "capture_cursor"))

        if len(self.audio_sources) == 1:
            self.combobox_audio2.set_active(self.combobox_audio.get_active())
            self.combobox_audio2.set_sensitive(False)
            self.switch_audio2.set_active(False)
            self.switch_audio2.set_sensitive(False)

        if video_toggled:
            self.btn_record.set_sensitive(True)
        else:
            self.btn_record.set_sensitive(False)

        if audio_toggled:
            self.switch_audio2.set_sensitive(True)
        else:
            self.switch_audio2.set_sensitive(False)
            self.switch_audio2.set_active(False)

    def save_state(self):
        logger.debug("Saving state.")
        video_toggled = self.switch_video.get_active()
        audio_toggled = self.switch_audio.get_active()
        audio2_toggled = self.switch_audio2.get_active()

        video_source = self.combobox_video.get_active()
        audio_source = self.combobox_audio.get_active()
        audio2_source = self.combobox_audio2.get_active()

        logger.debug("Saving state - sources: V ({0}), A_1 ({1}), A_2 ({2})".format(video_source,
                                                                                        audio_source,
                                                                                        audio2_source))

        self.config.set("main", "video_source", video_source)
        self.config.set("main", "audio_source", audio_source)
        self.config.set("main", "audio2_source", audio2_source)

        self.config.set("main", "video_toggled", video_toggled)
        self.config.set("main", "audio_toggled", audio_toggled)
        self.config.set("main", "audio2_toggled", audio2_toggled)

        self.config.set("main", "capture_cursor", self.capture_cursor)

        codec = self.combobox_codec.get_active()
        self.config.set("main", "codec", codec)

        counter = int(self.spinbutton_counter.get_value())
        self.config.set("main", "counter", counter)

        framerate = int(self.spinbutton_framerate.get_value())
        self.config.set("main", "framerate", framerate)

        self.config.write()

    def get_sources(self, audio = True):
        if audio:
            logger.debug("Getting Audio sources.")
            try:
                self.audio_sources = self.pa_q.get_audio_sources()
                if self.debug:
                    for src in self.audio_sources:
                        logger.debug(" Device found: ")
                        for item in src:
                            logger.debug("  - {0}".format(item))
            except:
                # Something went wrong, just fallback to no-sound
                logger.warning("Unable to find any audio devices.")
                self.audio_sources = [[0, _("Unknown"), _("Unknown")]]

        try:
            logger.debug("Getting Video sources.")
            self.video_sources = []
            self.default_screen = Gdk.Screen.get_default()
            logger.debug("Found {0} monitors.".format(self.default_screen.get_n_monitors()))
            for i in range(self.default_screen.get_n_monitors()):
                rect = self.default_screen.get_monitor_geometry(i)
                logger.debug("  Monitor {0} - X: {1}, Y: {2}, W: {3}, H: {4}".format(i,
                                                                                       rect.x,
                                                                                       rect.y,
                                                                                       rect.width,
                                                                                       rect.height))
                self.video_sources.append({"x": rect.x,
                                           "y": rect.y,
                                           "width": rect.width,
                                           "height": rect.height})
            #
            # Appen combined display too
            #
            if self.default_screen.get_n_monitors() > 1:
                self.video_sources.append({"x": 0,
                                           "y": 0,
                                           "width": self.default_screen.get_width(),
                                           "height": self.default_screen.get_height()})
        except:
            logger.warning("Unable to find any video sources.")
            self.video_sources = [_("Unknown")]

    #
    # TODO: Merge with get_sources?
    #
    def populate_widgets(self, audio = True):
        #
        # Audio first
        #
        if audio:
            for source in self.audio_sources:
                self.combobox_audio.append(None, source[2])
                self.combobox_audio2.append(None, source[2])

        #
        # Now video
        #

        self.combobox_video.remove_all()

        i = 1
        for s in self.video_sources:
            if i == len(self.video_sources) and len(self.video_sources) > 1:
                dsp_name = _("Combined ({w}x{h})".format(w = s['width'], h = s['height']))
            else:
                dsp_name = _("Display {n} ({w}x{h})".format(n = i, w = s['width'], h = s['height']))

            self.combobox_video.append(None, dsp_name)
            i += 1
