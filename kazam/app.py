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

from kazam.utils import *
from kazam.backend.constants import *
from kazam.backend.config import KazamConfig
from kazam.frontend.about_dialog import AboutDialog
from kazam.frontend.indicator import KazamIndicator
from kazam.frontend.window_region import RegionWindow
from kazam.frontend.done_recording import DoneRecording
from kazam.frontend.window_countdown import CountdownWindow

class KazamApp(GObject.GObject):

    def __init__(self, datadir, dist, debug, test, sound):
        GObject.GObject.__init__(self)
        logger.debug("Setting variables.")
        self.datadir = datadir
        self.debug = debug
        self.test = test
        self.dist = dist
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
        self.codec = 0
        self.main_x = 0
        self.main_y = 0
        self.countdown = None
        self.tempfile = ""
        self.recorder = None
        self.capture_cursor = True
        self.region_window = None
        self.region = None
        self.old_path = None
        self.timer_window = True
        self.in_countdown = False
        self.recording_paused = False

        if self.sound:
            self.pa_q = pulseaudio_q()
            self.pa_q.start()

        #
        # Setup config
        #
        self.config = KazamConfig()

        logger.debug("Connecting indicator signals.")
        self.indicator = KazamIndicator()
        self.indicator.connect("indicator-quit-request", self.cb_quit_request)
        self.indicator.connect("indicator-show-request", self.cb_show_request)
        self.indicator.connect("indicator-start-request", self.cb_start_request)
        self.indicator.connect("indicator-stop-request", self.cb_stop_request)
        self.indicator.connect("indicator-pause-request", self.cb_pause_request)
        self.indicator.connect("indicator-unpause-request", self.cb_unpause_request)

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
            self.populate_widgets(audio = False)

        self.window.show_all()
        self.restore_state()

        if not self.sound:
            self.combobox_audio.set_sensitive(False)
            self.combobox_audio2.set_sensitive(False)
            self.switch_audio.set_sensitive(False)
            self.switch_audio2.set_sensitive(False)
            self.volumebutton_audio.set_sensitive(False)
            self.volumebutton_audio2.set_sensitive(False)

        # self.keyboard_handler = KeyboardHandler(self.cb_keyboard_press)
        # self.keyboard_handler.start()

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
        try:
            os.remove(self.recorder.tempfile)
            os.remove("{0}.mux".format(self.recorder.tempfile))
        except:
            pass

        self.save_state()

        if self.sound:
            self.pa_q.end()

        Gtk.main_quit()

    def cb_show_request(self, indicator):
        logger.debug("Show requested, raising window.")
        self.window.show_all()
        self.window.present()
        print "Moving to:", self.main_x, self.main_y
        self.window.move(self.main_x, self.main_y)

    def cb_close_clicked(self, indicator):
        (self.main_x, self.main_y) = self.window.get_position()
        print "Recorded:", self.main_x, self.main_y
        self.window.hide()
        
    def cb_about_clicked(self, activated):
        AboutDialog(self.icons)    

    def cb_delete_event(self, widget, user_data):
        (self.main_x, self.main_y) = self.window.get_position()
        return self.window.hide_on_delete()

    def cb_video_switch(self, widget, user_data):
        if widget.get_active():
            logger.debug("Video ON.")
            self.combobox_video.set_sensitive(True)
            self.btn_record.set_sensitive(True)
        else:
            logger.debug("Video OFF.")
            self.combobox_video.set_sensitive(False)
            self.btn_record.set_sensitive(False)
            self.video_source = None


    def cb_audio_switch(self, widget, user_data):
        if widget.get_active():
            logger.debug("Audio1 ON.")
            self.combobox_audio.set_sensitive(True)
            self.switch_audio2.set_sensitive(True)
            self.volumebutton_audio.set_sensitive(True)
            self.audio_source = self.combobox_audio.get_active()
        else:
            logger.debug("Audio1 OFF.")
            self.combobox_audio.set_sensitive(False)
            self.volumebutton_audio.set_sensitive(False)
            self.combobox_audio2.set_sensitive(False)
            self.switch_audio2.set_sensitive(False)
            self.switch_audio2.set_active(False)
            self.volumebutton_audio2.set_sensitive(False)
            self.audio_source = None
            self.audio2_source = None

    def cb_audio2_switch(self, widget, user_data):
        if widget.get_active():
            logger.debug("Audio2 ON.")
            self.combobox_audio2.set_sensitive(True)
            self.volumebutton_audio2.set_sensitive(True)
            self.audio2_source  = self.combobox_audio2.get_active()
        else:
            logger.debug("Audio2 OFF.")
            self.audio2_source = None
            self.combobox_audio2.set_sensitive(False)
            self.volumebutton_audio2.set_sensitive(False)
            self.audio2_source = None

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
            if self.audio_source < len(self.audio_sources):
                self.audio2_source += 1
            else:
                self.audio2_source = 0

            #
            # This isn't probably the smartest idea, right?
            #
            self.combobox_audio2.set_active(self.audio2_source)
            self.switch_audio2.set_active(False)
            self.combobox_audio2.set_sensitive(False)

    def cb_video_changed(self, widget):
        logger.debug("Video changed.")
        self.video_source = self.combobox_video.get_active()
        logger.debug("New Video: {0}".format(self.video_sources[self.video_source]))

    def cb_codec_changed(self, widget):
        self.codec = self.combobox_codec.get_active()
        logger.debug("Encoding changed to {0}.".format(get_codec_name(self.codec)))

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
        chn = self.audio2_source_info[2].channels
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
        self.done_recording.show_all()
        logger.debug("Done recording signals connected.")
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
        except:
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

    def cb_cursor_switch(self, widget, user_data):
        if self.switch_cursor.get_active():
            logger.debug("Cursor capturing ON.")
            self.capture_cursor = True
        else:
            logger.debug("Cursor capturing OFF.")
            self.capture_cursor = False

    def cb_timer_switch(self, widget, user_data):
        if self.switch_timer.get_active():
            logger.debug("Timer Window ON.")
            self.timer_window = True
        else:
            logger.debug("Timer Window OFF.")
            self.timer_window = False

    def cb_region_toggled(self, widget):
        if self.btn_region.get_active():
            logger.debug("Region ON.")
            self.region_window = RegionWindow(self.region)
            self.region_window.connect("region-selected", self.cb_region_selected)
            self.region_window.connect("region-canceled", self.cb_region_canceled)
            self.window.set_sensitive(False)
        else:
            logger.debug("Region OFF.")
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
        self.window.set_sensitive(True)
        self.btn_region.set_active(False)

    # def cb_keyboard_press(self):
    #     print "YAY BACK"

    #
    # Other somewhat useful stuff ...
    #

    def run_counter(self):
        #
        # Annoyances with the menus
        #
        (self.main_x, self.main_y) = self.window.get_position()

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
            if self.audio_source is not None:
                audio_source = self.audio_sources[self.audio_source][1]
            else:
                audio_source = None

            if self.audio2_source is not None:
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
                                    self.capture_cursor,
                                    framerate,
                                    self.region,
                                    self.test,
                                    self.dist)

        self.recorder.connect("flush-done", self.cb_flush_done)
        self.countdown = CountdownWindow(self.indicator, show_window = self.timer_window)
        self.countdown.connect("counter-finished", self.cb_counter_finished)
        self.countdown.run(self.spinbutton_counter.get_value_as_int())
        logger.debug("Hiding main window.")
        self.window.hide()

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

        video_source = self.config.getint("main", "video_source")
        audio_source = self.config.getint("main", "audio_source")
        audio2_source = self.config.getint("main", "audio2_source")

        self.switch_video.set_active(video_toggled)

        self.main_x = self.config.getint("main", "last_x")
        self.main_y = self.config.getint("main", "last_y")

        self.window.move(self.main_x, self.main_y)

        logger.debug("Restoring state - sources: V ({0}), A_1 ({1}), A_2 ({2})".format(video_source,
                                                                                        audio_source,
                                                                                        audio2_source))
        self.video_source = video_source

        self.combobox_video.set_active(video_source)
        self.combobox_video.set_sensitive(video_toggled)

        if self.sound:
            self.switch_audio.set_active(audio_toggled)
            self.switch_audio2.set_active(audio2_toggled)


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

            if len(self.audio_sources) == 1:
                self.combobox_audio2.set_active(self.combobox_audio.get_active())
                self.combobox_audio2.set_sensitive(False)
                self.switch_audio2.set_active(False)
                self.switch_audio2.set_sensitive(False)

            if audio_toggled:
                self.switch_audio2.set_sensitive(True)
                self.audio_source = audio_source
            else:
                self.switch_audio2.set_sensitive(False)
                self.switch_audio2.set_active(False)
                self.audio_source = None

            if audio2_toggled:
                self.audio2_source = audio2_source
            else:
                self.audio2_source = None


        codec = self.config.getint("main", "codec")
        self.combobox_codec.set_active(codec)
        self.codec = codec

        self.spinbutton_counter.set_value(self.config.getfloat("main", "counter"))
        self.spinbutton_framerate.set_value(self.config.getfloat("main", "framerate"))

        self.switch_cursor.set_active(self.config.getboolean("main", "capture_cursor"))
        self.switch_timer.set_active(self.config.getboolean("main", "timer_window"))

        if video_toggled:
            self.btn_record.set_sensitive(True)
        else:
            self.btn_record.set_sensitive(False)


    def save_state(self):
        logger.debug("Saving state.")
        video_toggled = self.switch_video.get_active()
        video_source = self.combobox_video.get_active()

        if self.sound:
            audio_toggled = self.switch_audio.get_active()
            audio2_toggled = self.switch_audio2.get_active()
            audio_source = self.combobox_audio.get_active()
            audio2_source = self.combobox_audio2.get_active()
            self.config.set("main", "audio_source", audio_source)
            self.config.set("main", "audio2_source", audio2_source)
            self.config.set("main", "audio_toggled", audio_toggled)
            self.config.set("main", "audio2_toggled", audio2_toggled)

        self.config.set("main", "video_source", video_source)
        self.config.set("main", "video_toggled", video_toggled)

        self.config.set("main", "capture_cursor", self.capture_cursor)
        self.config.set("main", "timer_window", self.timer_window)

        self.config.set("main", "last_x", self.main_x)
        self.config.set("main", "last_y", self.main_y)


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

        if audio:
            for source in self.audio_sources:
                self.combobox_audio.append(None, source[2])
                self.combobox_audio2.append(None, source[2])

        self.combobox_video.remove_all()

        i = 1
        for s in self.video_sources:
            if i == len(self.video_sources) and len(self.video_sources) > 1:
                dsp_name = _("Combined ({w}x{h})".format(w = s['width'], h = s['height']))
            else:
                dsp_name = _("Display {n} ({w}x{h})".format(n = i, w = s['width'], h = s['height']))

            self.combobox_video.append(None, dsp_name)
            i += 1

        self.combobox_codec.append(None, "Gstreamer - VP8/WebM")
        self.combobox_codec.append(None, "GStreamer - H264/MP4")
