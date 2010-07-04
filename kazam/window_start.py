#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       window_start.py
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

import gtk

def populate_combobox_video(combobox_video):
    list_store = gtk.ListStore(str)
    list_store.append(["Screen"])
    
    combobox_video.set_model(list_store)
    text = gtk.CellRendererText()
    combobox_video.pack_start(text)
    combobox_video.add_attribute(text, "text", 0)
    combobox_video.set_active(0)

def populate_combobox_audio(combobox_audio):
    list_store = gtk.ListStore(str)
    list_store.append(["Microphone"])
    
    combobox_audio.set_model(list_store)
    text = gtk.CellRendererText()
    combobox_audio.pack_start(text)
    combobox_audio.add_attribute(text, "text", 0)
    combobox_audio.set_active(0)
