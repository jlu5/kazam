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
import math
logger = logging.getLogger("Main")

from subprocess import Popen
from gi.repository import Gtk, Gdk, GObject
from gettext import gettext as _

from kazam.utils import *
from kazam.backend.constants import *
from kazam.backend.config import KazamConfig
from kazam.backend.gstreamer import detect_codecs, get_codec
from kazam.frontend.about_dialog import AboutDialog
from kazam.frontend.indicator import KazamIndicator
from kazam.frontend.window_region import RegionWindow
from kazam.frontend.done_recording import DoneRecording
from kazam.frontend.window_countdown import CountdownWindow

class KazamApp(GObject.GObject):

    def __init__(self, datadir, dist, debug, test, sound, silent):
        GObject.GObject.__init__(self)
        logger.debug("Setting variables.")

        self.startup = True
        self.datadir = datadir
        self.debug = debug
        self.test = test
        self.dist = dist
        self.silent = silent
        self.sound = not sound     # Parameter is called nosound and if true, then we don't have sound.
                                   # Tricky parameters are tricky!
        self.setup_translations()

        if self.sound:
            try:
                from kazam.pulseaudio.pulseaudio import pulseaudio_q
                self.sound = True
            except:
                logger.warning("Pulse Audio Failed to load. Sound recording disabled.")
                self.sound = False

        self.icons = Gtk.IconTheme.get_default()
        self.icons.append_search_path(os.path.join(datadir,"icons", "48x48", "apps"))
        self.icons.append_search_path(os.path.join(datadir,"icons", "16x16", "apps"))

        # Initialize all the variables

        self.video_sources = []
        self.video_source = 0
        self.audio_source = 0
        self.audio2_source = 0
        self.framerate = 0
        self.counter = 0
        self.codec = 0
        self.main_x = 0
        self.main_y = 0
        self.countdown = None
        self.tempfile = ""
        self.recorder = None
        self.cursor = True
        self.region_window = None
        self.region = None
        self.old_path = None
        self.countdown_splash = True
        self.in_countdown = False
        self.recording_paused = False
        self.recording = False
        self.region_toggled = False
        self.advanced = False

        if self.sound:
            self.pa_q = pulseaudio_q()
            self.pa_q.start()

        #
        # Setup config
        #
        self.config = KazamConfig()

        self.read_config()

        logger.debug("Connecting indicator signals.")
        logger.debug("Starting in silent mode: {0}".format(self.silent))
        self.indicator = KazamIndicator(self.silent)
        self.indicator.connect("indicator-quit-request", self.cb_quit_request)
        self.indicator.connect("indicator-show-request", self.cb_show_request)
        self.indicator.connect("indicator-start-request", self.cb_start_request)
        self.indicator.connect("indicator-stop-request", self.cb_stop_request)
        self.indicator.connect("indicator-pause-request", self.cb_pause_request)
        self.indicator.connect("indicator-unpause-request", self.cb_unpause_request)
        self.indicator.connect("indicator-about-request", self.cb_about_request)

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
                setattr(self, name, w)
            else:
                logger.debug("Unable to get name for '%s'" % w)

        # If these are added in glade, something weeird happens - investigate! :)
        self.volume_adjustment = Gtk.Adjustment(0, 0, 60, 1, 3, 0)
        self.volume2_adjustment = Gtk.Adjustment(0, 0, 60, 1, 3, 0)
        self.framerate_adjustment = Gtk.Adjustment(25, 1, 60, 1, 5, 0)
        self.counter_adjustment = Gtk.Adjustment(5, 0, 65, 1, 5, 0)

        self.volumebutton_audio.set_adjustment(self.volume_adjustment)
        self.volumebutton_audio2.set_adjustment(self.volume2_adjustment)
        self.spinbutton_framerate.set_adjustment(self.framerate_adjustment)
        self.spinbutton_counter.set_adjustment(self.counter_adjustment)

        renderer_text = Gtk.CellRendererText()
        self.combobox_codec.pack_start(renderer_text, True)
        self.combobox_codec.add_attribute(renderer_text, "text", 1)

        #
        # Take care of screen size changes.
        #
        self.default_screen = Gdk.Screen.get_default()
        self.default_screen.connect("size-changed", self.cb_screen_size_changed)
        self.window.connect("configure-event", self.cb_configure_event)

        # Fetch sources info, take care of all the widgets and saved settings and show main window
        if self.sound:
            self.get_sources()
            self.populate_widgets()
        else:
            self.get_sources(audio = False)
            self.populate_widgets(screen_only = True)

        if not self.silent:
            self.window.show_all()
        else:
            logger.info("Starting in silent mode:\n  SUPER-CTRL-W to toggle main window.\n  SUPER-CTRL-Q to quit.")

        self.restore_state()

        if not self.sound:
            self.combobox_audio.set_sensitive(False)
            self.combobox_audio2.set_sensitive(False)
            self.volumebutton_audio.set_sensitive(False)
            self.volumebutton_audio2.set_sensitive(False)

        self.startup = False

    #
    # Callbacks, go down here ...
    #

    def cb_screen_size_changed(self, screen):
        logger.debug("Screen size changed.")
        old_source = self.video_source
        old_num = len(self.video_sources)
        self.get_sources(audio = False)
        self.populate_widgets(screen_only = True)
        if old_source > old_num:
            old_source = 0
        self.combobox_video.set_active(old_source)

    def cb_configure_event(self, widget, event):
        if event.type == Gdk.EventType.CONFIGURE:
            #
            # When you close main window up to 5 configure events fire up some of them have X and Y set to 0 ?!?
            #
            if event.x or event.y > 0:
                self.main_x = event.x
                self.main_y = event.y


    def cb_quit_request(self, indicator):
        logger.debug("Quit requested.")
        (self.main_x, self.main_y) = self.window.get_position()
        try:
            os.remove(self.recorder.tempfile)
            os.remove("{0}.mux".format(self.recorder.tempfile))
        except OSError:
            logger.info("Unable to delete one of the temporary files. Check your temporary directory.")
        except AttributeError:
            pass
        self.save_state()
        if self.sound:
            self.pa_q.end()

        Gtk.main_quit()

    def cb_show_request(self, indicator):
        if not self.window.get_property("visible"):
            logger.debug("Show requested, raising window.")
            self.window.show_all()
            self.window.present()
            self.window.move(self.main_x, self.main_y)
        else:
            self.window.hide()

    def cb_close_clicked(self, indicator):
        (self.main_x, self.main_y) = self.window.get_position()
        self.window.hide()

    def cb_about_request(self, activated):
        AboutDialog(self.icons)

    def cb_delete_event(self, widget, user_data):
        self.cb_quit_request(None)

    def cb_audio_changed(self, widget):
        logger.debug("Audio Changed.")

        self.audio_source = self.combobox_audio.get_active()
        logger.debug("  - A_1 {0}".format(self.audio_source))

        if self.audio_source:
            pa_audio_idx =  self.audio_sources[self.audio_source][0]
            self.pa_q.set_source_mute_by_index(pa_audio_idx, 0)

            logger.debug("  - PA Audio1 IDX: {0}".format(pa_audio_idx))
            self.audio_source_info = self.pa_q.get_source_info_by_index(pa_audio_idx)
            if len(self.audio_source_info) > 0:
                val = self.pa_q.cvolume_to_dB(self.audio_source_info[2])
                if math.isinf(val):
                    vol = 0
                else:
                    vol = 60 + val
                self.volumebutton_audio.set_value(vol)
            else:
                logger.debug("Error getting volume info for Audio 1")

            if len(self.audio_source_info):
               logger.debug("New Audio1:\n  {0}".format(self.audio_source_info[3]))
            else:
                logger.debug("New Audio1:\n  Error retrieving data.")

            if self.audio_source and self.audio_source == self.audio2_source:
                if self.audio_source < len(self.audio_sources):
                    self.audio2_source += 1
                else:
                    self.audio2_source = 0
                self.combobox_audio2.set_active(0)

            self.volumebutton_audio.set_sensitive(True)
            self.combobox_audio2.set_sensitive(True)
        else:
            self.volumebutton_audio.set_sensitive(False)
            self.combobox_audio2.set_sensitive(False)
            self.combobox_audio2.set_active(0)
            logger.debug("Audio1 OFF.")

    def cb_audio2_changed(self, widget):
        logger.debug("Audio2 Changed.")

        self.audio2_source = self.combobox_audio2.get_active()
        logger.debug("  - A_2 {0}".format(self.audio2_source))

        if self.audio2_source:
            pa_audio2_idx =  self.audio_sources[self.audio2_source][0]
            self.pa_q.set_source_mute_by_index(pa_audio2_idx, 0)

            logger.debug("  - PA Audio2 IDX: {0}".format(pa_audio2_idx))
            self.audio2_source_info = self.pa_q.get_source_info_by_index(pa_audio2_idx)

            if len(self.audio2_source_info) > 0:
                val = self.pa_q.cvolume_to_dB(self.audio2_source_info[2])
                if math.isinf(val):
                    vol = 0
                else:
                    vol = 60 + val
                self.volumebutton_audio2.set_value(vol)
            else:
                logger.debug("Error getting volume info for Audio 1")

            if len(self.audio2_source_info):
                logger.debug("New Audio2:\n  {0}".format(self.audio2_source_info[3]))
            else:
                logger.debug("New Audio2:\n  Error retrieving data.")

            if self.audio_source and self.audio_source == self.audio2_source:
                if self.audio_source < len(self.audio_sources):
                    self.audio2_source += 1
                else:
                    self.audio2_source = 0

                self.combobox_audio2.set_active(0)
            self.volumebutton_audio2.set_sensitive(True)
        else:
            self.volumebutton_audio2.set_sensitive(False)
            logger.debug("Audio2 OFF.")

    def cb_video_changed(self, widget):
        logger.debug("Video changed.")
        self.video_source = self.combobox_video.get_active()
        logger.debug("New Video: {0}".format(self.video_sources[self.video_source]))

    def cb_codec_changed(self, widget):
        i = widget.get_active()
        model = widget.get_model()
        iter = model.get_iter(i)
        self.codec = model.get_value(iter, 0)
        logger.debug('Codec selected: {0} - {1}'.format(get_codec(self.codec)[2], self.codec))

    def cb_start_request(self, widget):
        logger.debug("Start recording selected.")
        self.run_counter()

    def cb_record_clicked(self, widget):
        logger.debug("Record clicked, invoking Screencast.")
        self.run_counter()

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
        chn = self.audio_source_info[2].channels
        cvol = self.pa_q.dB_to_cvolume(chn, value-60)
        self.pa_q.set_source_volume_by_index(pa_idx, cvol)

    def cb_counter_finished(self, widget):
        logger.debug("Counter finished.")
        self.in_countdown = False
        self.countdown = None
        self.indicator.menuitem_finish.set_label(_("Finish recording"))
        self.indicator.menuitem_pause.set_sensitive(True)
        self.indicator.blink_set_state(BLINK_STOP)
        self.indicator.start_recording()
        self.recorder.start_recording()

    def cb_stop_request(self, widget):
        self.recording = False
        if self.in_countdown:
            logger.debug("Cancel countdown request.")
            self.countdown.cancel_countdown()
            self.countdown = None
            self.indicator.menuitem_finish.set_label(_("Finish recording"))
            self.window.set_sensitive(True)
            self.window.show()
            self.window.present()
        else:
            if self.recording_paused:
                self.recorder.unpause_recording()
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
        logger.debug("Done recording signals connected.")
        self.done_recording.show_all()
        self.window.set_sensitive(False)

    def cb_pause_request(self, widget):
        logger.debug("Pause requested.")
        self.recording_paused = True
        self.recorder.pause_recording()

    def cb_unpause_request(self, widget):
        logger.debug("Unpause requested.")
        self.recording_paused = False
        self.recorder.unpause_recording()

    def cb_save_done(self, widget, result):
        logger.debug("Save Done, result: {0}".format(result))
        self.old_path = result
        self.window.set_sensitive(True)
        self.window.show_all()
        self.window.present()
        self.window.move(self.main_x, self.main_y)

    def cb_save_cancel(self, widget):
        try:
            logger.debug("Save canceled, removing {0}".format(self.tempfile))
            os.remove(self.tempfile)
        except OSError:
            logger.info("Failed to remove tempfile {0}".format(self.tempfile))
        except AttributeError:
            logger.info("Failed to remove tempfile {0}".format(self.tempfile))
            pass

        self.window.set_sensitive(True)
        self.window.show_all()
        self.window.present()
        self.window.move(self.main_x, self.main_y)

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

    def cb_switch_silent(self, widget, user_data):
        self.silent = not self.silent
        logger.debug("Silent mode: {0}.".format(self.silent))

    def cb_switch_cursor(self, widget, user_data):
        self.cursor = not self.cursor
        logger.debug("Cursor capture: {0}.".format(self.cursor))

    def cb_switch_countdown_splash(self, widget, user_data):
        self.countdown_splash = not self.countdown_splash
        logger.debug("Coutndown splash: {0}.".format(self.countdown_splash))

    def cb_switch_codecs(self, widget, user_data):
        self.advanced = not self.advanced
        self.populate_codecs()
        logger.debug("Advanced codecs: {0}".format(self.advanced))

    def cb_region_toggled(self, widget):
        if self.btn_region.get_active():
            logger.debug("Region ON.")
            self.region_window = RegionWindow(self.region)
            self.region_window.connect("region-selected", self.cb_region_selected)
            self.region_window.connect("region-canceled", self.cb_region_canceled)
            self.window.set_sensitive(False)
            self.region_toggled = True
        else:
            logger.debug("Region OFF.")
            self.region_window.window.destroy()
            self.region_window = None
            self.region_toggled = False

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
        self.window.set_sensitive(True)
        self.btn_region.set_active(False)
        self.region_toggled = False

    #
    # Other somewhat useful stuff ...
    #

    def run_counter(self):
        #
        # Annoyances with the menus
        #
        (main_x, main_y) = self.window.get_position()
        if main_x and main_y:
            self.main_x = main_x
            self.main_y = main_y

        self.indicator.recording = True
        self.indicator.menuitem_start.set_sensitive(False)
        self.indicator.menuitem_pause.set_sensitive(False)
        self.indicator.menuitem_finish.set_sensitive(True)
        self.indicator.menuitem_show.set_sensitive(False)
        self.indicator.menuitem_quit.set_sensitive(False)
        self.indicator.menuitem_finish.set_label(_("Cancel countdown"))
        self.in_countdown = True

        from kazam.backend.gstreamer import Screencast

        self.recorder = Screencast(self.debug)
        self.indicator.blink_set_state(BLINK_START)

        if self.sound:
            if self.audio_source > 0:
                audio_source = self.audio_sources[self.audio_source][1]
            else:
                audio_source = None

            if self.audio2_source > 0:
                audio2_source = self.audio_sources[self.audio2_source][1]
            else:
                audio2_source = None
        else:
            audio_source = None
            audio2_source = None

        if self.video_source is not None:
            video_source = self.video_sources[self.video_source]
        else:
            video_source = None

        framerate = self.spinbutton_framerate.get_value_as_int()
        self.recorder.setup_sources(video_source,
                                    audio_source,
                                    audio2_source,
                                    self.codec,
                                    self.cursor,
                                    framerate,
                                    self.region if self.region_toggled else None,
                                    self.test,
                                    self.dist)

        self.recorder.connect("flush-done", self.cb_flush_done)
        self.countdown = CountdownWindow(self.indicator, show_window = self.countdown_splash)
        self.countdown.connect("counter-finished", self.cb_counter_finished)
        self.countdown.run(self.spinbutton_counter.get_value_as_int())
        self.recording = True
        logger.debug("Hiding main window.")
        self.window.hide()

    def setup_translations(self):
        gettext.bindtextdomain("kazam", "/usr/share/locale")
        gettext.textdomain("kazam")
        try:
            locale.setlocale(locale.LC_ALL, "")
        except Exception, e:
            logger.exception("setlocale failed")

    def read_config (self):
        video_toggled = self.config.getboolean("main", "video_toggled")

        self.video_source = self.config.getint("main", "video_source")
        self.audio_source = self.config.getint("main", "audio_source")
        self.audio2_source = self.config.getint("main", "audio2_source")

        self.main_x = self.config.getint("main", "last_x")
        self.main_y = self.config.getint("main", "last_y")

        self.codec = self.config.getint("main", "codec")

        self.counter = self.config.getfloat("main", "counter")
        self.framerate = self.config.getfloat("main", "framerate")

        self.cursor = self.config.getboolean("main", "capture_cursor")
        self.countdown_splash = self.config.getboolean("main", "countdown_splash")
        self.advanced = self.config.getboolean("main", "advanced")
        self.silent = self.config.getboolean("main", "silent")

    def restore_state (self):

        logger.debug("Restoring state - sources: V ({0}), A_1 ({1}), A_2 ({2})".format(self.video_source,
                                                                                        self.audio_source,
                                                                                        self.audio2_source))
        self.window.move(self.main_x, self.main_y)

        self.combobox_video.set_active(self.video_source)
        self.combobox_video.set_sensitive(True)

        if self.sound:
            logger.debug("Getting volume info.")

            self.combobox_audio.set_active(self.audio_source)
            self.combobox_audio2.set_active(self.audio2_source)

            if self.audio_source:
                self.volumebutton_audio.set_sensitive(True)
                self.combobox_audio2.set_sensitive(True)
            else:
                self.volumebutton_audio.set_sensitive(False)
                self.combobox_audio2.set_sensitive(False)

            if self.audio2_source:
                self.volumebutton_audio2.set_sensitive(True)
            else:
                self.volumebutton_audio2.set_sensitive(False)

        if self.advanced:
            self.switch_codecs.set_active(True)
            self.advanced = True
        if self.cursor:
            self.switch_cursor.set_active(True)
            self.cursor = True
        if self.countdown_splash:
            self.switch_countdown_splash.set_active(True)
            self.countdown_splash = True
        if self.silent:
            self.switch_silent.set_active(True)
            self.silent = True

        self.spinbutton_counter.set_value(self.counter)
        self.spinbutton_framerate.set_value(self.framerate)

        codec_model = self.combobox_codec.get_model()

        #
        # Crappy code below ...
        #
        cnt = 0
        bingo = False
        for entry in codec_model:
            if self.codec == entry[0]:
                bingo = True
                break
            cnt += 1
        if not bingo:
            cnt = 0

        #
        # No, I wasn't kidding ...
        #

        codec_iter = codec_model.get_iter(cnt)
        self.combobox_codec.set_active_iter(codec_iter)
        self.codec = codec_model.get_value(codec_iter, 0)

    def save_state(self):
        logger.debug("Saving state.")
        video_source = self.combobox_video.get_active()

        if self.sound:
            audio_source = self.combobox_audio.get_active()
            audio2_source = self.combobox_audio2.get_active()
            self.config.set("main", "audio_source", audio_source)
            self.config.set("main", "audio2_source", audio2_source)

        self.config.set("main", "video_source", video_source)

        self.config.set("main", "capture_cursor", self.cursor)
        self.config.set("main", "countdown_splash", self.countdown_splash)

        self.config.set("main", "last_x", self.main_x)
        self.config.set("main", "last_y", self.main_y)


        codec = self.combobox_codec.get_active()
        codec_model = self.combobox_codec.get_model()
        codec_model_iter = codec_model.get_iter(codec)
        codec_value = codec_model.get_value(codec_model_iter, 0)
        self.config.set("main", "codec", codec_value)

        self.config.set("main", "advanced", self.advanced)

        counter = int(self.spinbutton_counter.get_value())
        self.config.set("main", "counter", counter)

        framerate = int(self.spinbutton_framerate.get_value())
        self.config.set("main", "framerate", framerate)

        self.config.set("main", "silent", self.silent)

        self.config.write()

    def get_sources(self, audio = True):
        if audio:
            logger.debug("Getting Audio sources.")
            try:
                self.audio_sources = self.pa_q.get_audio_sources()
                self.audio_sources.insert(0, [])
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
    def populate_widgets(self, screen_only = False):

        self.combobox_video.remove_all()
        i = 1
        for s in self.video_sources:
            if i == len(self.video_sources) and len(self.video_sources) > 1:
                dsp_name = _("Combined ({w}x{h})".format(w = s['width'], h = s['height']))
            else:
                dsp_name = _("Display {n} ({w}x{h})".format(n = i, w = s['width'], h = s['height']))

            self.combobox_video.append(None, dsp_name)
            i += 1

        if not screen_only:
            for source in self.audio_sources:
                if not len(source):
                    self.combobox_audio.append(None, "Off")
                    self.combobox_audio2.append(None, "Off")
                else:
                    self.combobox_audio.append(None, source[2])
                    self.combobox_audio2.append(None, source[2])

            self.populate_codecs()


    def populate_codecs(self):
        old_model = self.combobox_codec.get_model()
        old_model = None

        codec_model = Gtk.ListStore(int, str)

        codecs = detect_codecs()

        for codec in codecs:
            if CODEC_LIST[codec][4] and self.advanced:
                codec_model.append([CODEC_LIST[codec][0], CODEC_LIST[codec][2]])
            elif not CODEC_LIST[codec][4]:
                codec_model.append([CODEC_LIST[codec][0], CODEC_LIST[codec][2]])

        self.combobox_codec.set_model(codec_model)

        if not self.startup:
            self.combobox_codec.set_active(0)



