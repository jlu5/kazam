#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       utils.py
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
import sys
from threading import Thread

def menubar_from_dict(self, dictionary):
    """
    Takes a dictionary in the form:
    
    [{
        name:{
        connect:(signal, callback)
        children: [{
                    name:{
                    connect:(signal, callback)
                    children: {
                        ...
                        }
                    }]
    }]
    
    and converts it to a gtk.Menubar hierachy.
    """
    menubar = gtk.MenuBar()
    
    for menuitem_data in dictionary:
        name = menuitem_data["name"]
        menuitem = gtk.MenuItem(name, True)
        menubar.append(menuitem)
        
        if menuitem_data.has_key("connect"):
            (signal, callback) = menuitem_data["connect"]
            menuitem.connect(signal, getattr(self, callback))
            
        if menuitem_data.has_key("children"):
            sub_dictionary = menuitem_data["children"]
            menu = gtk.Menu()
            menuitem.set_submenu(menu)
            
            for sub_menuitem_data in sub_dictionary:
                sub_name = sub_menuitem_data["name"]
                sub_menuitem = gtk.MenuItem(sub_name, True)
                menu.append(sub_menuitem)
                
                if sub_menuitem_data.has_key("connect"):
                    (signal, callback) = sub_menuitem_data["connect"]
                    sub_menuitem.connect(signal, getattr(self, callback))
                
    menubar.show_all()
    
    return menubar
    
def setup_ui(self, path):
    self.builder = gtk.Builder()
    self.builder.add_from_file(path)
    self.builder.connect_signals(self)
    for o in self.builder.get_objects():
        if issubclass(type(o), gtk.Buildable):
            name = gtk.Buildable.get_name(o)
            setattr(self, name, o)
        else:
            print >> sys.stderr, "WARNING: can not get name for '%s'" % o    
    
def create_wait_thread(target, args=False):
    """
    Create a thread and wait until it is completed
    """
    if args:
        thread = Thread(target=target, args=args)
    else:
        thread = Thread(target=target)
    thread.start()
    while thread.isAlive():
        gtk.main_iteration()

def remove_list_dups(seq, idfun=None):  
    if idfun is None: 
        def idfun(x): return x 
    seen = {} 
    result = [] 
    for item in seq: 
        marker = idfun(item) 
        if marker in seen: continue 
        seen[marker] = 1 
        result.append(item) 
    return result
    
