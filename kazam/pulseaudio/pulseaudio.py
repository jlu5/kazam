#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       pulseaudio.py
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

import time

from error_handling import *

try:
    from ctypes_pulseaudio import *
except:
    raise PAError(PA_LOAD_ERROR, "Unable to load pulseaudio wrapper lib. Is PulseAudio installed?")

class PulseAudio_Q:
    def __init__(self):
        """PulseAudio_Q constructor.

        Initializes and sets all the necessary startup variables.

        Args:
            None
        Returns:
            None
        Raises:
            None
        """

        self.pa_state = -1
        self.sources = []
        self._sources = []
        self.pa_status = PA_STOPPED

        #
        # Making sure that we don't lose references to callback functions
        #
        self._pa_state_cb = pa_context_notify_cb_t(self.pa_state_cb)
        self._pa_sourcelist_cb = pa_source_info_cb_t(self.pa_sourcelist_cb)

    def pa_state_cb(self, context, userdata):
        """Reads PulseAudio context state.

        Sets self.pa_state depending on the pa_context_state and
        raises an error if unable to get the state from PulseAudio.

        Args:
            context: PulseAudio context.
            userdata: n/a.

        Returns:
            Zero on success or raises an exception.

        Raises:
            PAError, PA_GET_STATE_ERROR if pa_context_get_state() failed.
        """

        try:
            state = pa_context_get_state(context)

            if state in [PA_CONTEXT_UNCONNECTED, PA_CONTEXT_CONNECTING, PA_CONTEXT_AUTHORIZING,
                         PA_CONTEXT_SETTING_NAME]:
                self.pa_state = 0
            elif state == PA_CONTEXT_FAILED:
                self.pa_state = 2
            elif state == PA_CONTEXT_READY:
                self.pa_state = 1
        except:
            raise PAError(PA_GET_STATE_ERROR, "Unable to read context state.")

        return  0

    def pa_sourcelist_cb(self, context, source_info, eol, userdata):
        """Source list callback function

        Called by mainloop thread each time list of audio sources is requestd.
        All the parameters to this functions are passed to it automatically by
        the caller.

        Args:
            context: PulseAudio context.
            source_info: data returned from mainloop.
            eol: End Of List marker if set to non-zero there is no more date
            to read and we should bail out.
            userdata: n/a.

        Returns:
            self.source_list: Contains list of all Pulse Audio sources.
            self.pa_status: PA_WORKING or PA_FINISHED

        Raises:
            None
        """

        if eol == 0:
            self.pa_status = PA_WORKING
            self._sources.append([source_info.contents.index,
                                 source_info.contents.name,
                                 source_info.contents.description])
        else:
            self.pa_status = PA_FINISHED

        return 0

    def start(self):
        """Starts PulseAudio threaded mainloop.

        Creates mainloop, mainloop API and context objects and connects
        to the PulseAudio server.

        Args:
            None

        Returns:
            None

        Raises:
            PAError, PA_STARTUP_ERROR - if unable to create PA objects.
            PAError, PA_UNABLE_TO_CONNECT - if connection to PA fails.
            PAError, PA_UNABLE_TO_CONNECT2 - if call to connect() fails.
            PAError, PA_MAINLOOP_START_ERROR - if not able to start mainloop.
        """
        try:
            self.pa_ml = pa_threaded_mainloop_new()
            self.pa_mlapi = pa_threaded_mainloop_get_api(self.pa_ml)
            self.pa_ctx = pa_context_new(self.pa_mlapi, "kazam-pulse")
        except:
            raise PAError(PA_STARTUP_ERROR, "Unable to access PulseAudio API.")

        try:
            if pa_context_connect(self.pa_ctx, None, 0, None) != 0:
                raise PAError(PA_UNABLE_TO_CONNECT, "Unable to connect to PulseAudio server.")
        except:
            raise PAError(PA_UNABLE_TO_CONNECT2, "Unable to initiate connection to PulseAudio server.")

        try:
            pa_context_set_state_callback(self.pa_ctx, self._pa_state_cb, None)
            pa_threaded_mainloop_start(self.pa_ml)
            pa_context_get_state(self.pa_ctx)
        except:
            raise PAError(PA_MAINLOOP_START_ERROR, "Unable to start mainloop.")

    def end(self):
        """Disconnects from PulseAudio server.

        Disconnects from PulseAudio server, it should be called after all the
        operations are finished.

        Args:
            None

        Returns:
            None

        Raises:
            PAError, PA_MAINLOOP_END_ERROR - if not able to disconnect.
        """
        try:
            pa_context_disconnect(self.pa_ctx)
        except:
            raise PAError(PA_MAINLOOP_END_ERROR, "Unable to end mainloop.")

    def get_audio_sources(self):
        try:
            pa_context_get_source_info_list(self.pa_ctx, self._pa_sourcelist_cb, None);
            t = time.clock()
            while time.clock() - t < 5:
                if self.pa_status == PA_FINISHED:
                    self.sources = self._sources
                    self._sources = []
                    return self.sources
            raise PAError(PA_GET_SOURCES_TIMEOUT, "Unable to get sources, operation timed out.")
        except:
            raise PAError(PA_GET_SOURCES_ERROR, "Unable to get sources.")

