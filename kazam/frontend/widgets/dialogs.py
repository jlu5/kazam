#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       authenticate.py
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

import glib
import gtk
import gobject
import webbrowser
import os
import logging

from gettext import gettext as _

from kazam.utils import *
from kazam.version import VERSION
from kazam.backend.constants import *

AUTHORS = """
Andrew Higginson <rugby471@gmail.com>
David Klasinc <bigwhale@lubica.net>
"""

ARTISTS = """
Robert McKenna <ttk1opc@yahoo.com>
Andrew Higginson <rugby471@gmail.com>
"""


def new_about_dialog(icons):
    dialog = gtk.AboutDialog()
    dialog.set_name(_("Kazam Screencaster"))
    dialog.set_comments(_("Record a video of activity on your screen."))
    dialog.set_version(VERSION)
    dialog.set_copyright("© 2010 Andrew Higginson")
    dialog.set_website("http://launchpad.net/kazam")
    dialog.set_authors(AUTHORS.split("\n"))
    dialog.set_artists(ARTISTS.split("\n"))
    try:
        icon = icons.load_icon("kazam", 96, ())
        dialog.set_logo(icon)
    except glib.GError:
        # Not important, we just don't get to show our lovely logo.. :)
        pass
    dialog.show_all()
    dialog.set_position(gtk.WIN_POS_CENTER_ALWAYS)
    result = dialog.run()
    dialog.hide()
        

def new_save_dialog(title, codec, parent=None):
    dialog = gtk.FileChooserDialog(title=title, parent=parent, 
                        action=gtk.FILE_CHOOSER_ACTION_SAVE, 
                        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
                        gtk.STOCK_SAVE, gtk.RESPONSE_OK))
    
    if codec == CODEC_VP8:
        dialog.set_current_name("%s.webm" % _("Untitled_Screencast"))
    elif codec == CODEC_H264:
        dialog.set_current_name("%s.mkv" % _("Untitled_Screencast"))

    dialog.set_do_overwrite_confirmation(True)
    
    # Try to set the default folder to be ~/Videos, otherwise 
    # ~/Documents, otherwise ~/
    video_path = os.path.expanduser("~/Videos/")
    documents_path = os.path.expanduser("~/Documents/")
    home_path = os.path.expanduser("~/")
    if os.path.isdir(video_path):
        dialog.add_shortcut_folder(video_path)
        dialog.set_current_folder(video_path)
    elif os.path.isdir(documents_path):
        dialog.set_current_folder(documents_path)
    elif os.path.isdir(home_path):
        dialog.set_current_folder(home_path)
    
    dialog.show_all()                                      
    result = dialog.run()
    dialog.hide()
    return dialog, result
    
def new_linkbutton_dialog(uri, primary, secondary=None, parent=None):
    dialog = gtk.MessageDialog(parent=parent, type=gtk.MESSAGE_INFO,
                    buttons=gtk.BUTTONS_OK, message_format=primary)
            
    if secondary:
        dialog.format_secondary_markup(secondary)
                
    hbox = gtk.HBox()
    linkbutton = gtk.LinkButton(uri, uri)
    
    vbox = dialog.get_content_area().get_children()[0].get_children()[1]
    hbox.pack_start(linkbutton, False, False)
    vbox.pack_start(hbox, False, False)
                
    dialog.show_all()                                      
    result = dialog.run()
    dialog.hide()
    return dialog
    
def new_info_dialog(primary, secondary=None, parent=None):
    dialog = gtk.MessageDialog(parent=parent, type=gtk.MESSAGE_INFO,
                    buttons=gtk.BUTTONS_OK, message_format=primary)
                
    if secondary:
        dialog.format_secondary_markup(secondary)
                
    dialog.show_all()                                      
    result = dialog.run()
    dialog.hide()
    return dialog

class AuthenticateDialog(gobject.GObject):
    
    __gsignals__ = {
    "save-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           ( ),),
    "edit-requested"     : (gobject.SIGNAL_RUN_LAST,
                           gobject.TYPE_NONE,
                           [gobject.TYPE_PYOBJECT],)
    }

    
    (ACTION_LOGIN, ACTION_REGISTER, ACTION_CANCEL) = range(3)
    
    def __init__(self, datadir, name, icontheme, icons, register_url):
        super(AuthenticateDialog, self).__init__()
        
        # Setup UI
        setup_ui(self, os.path.join(datadir, "ui", "authenticate.ui"))        
        
        self.action = self.ACTION_LOGIN
        self.window = self.window_authenticate
        self.register_url = register_url
        
        (small_icon, large_icon) = icons
        
        if not register_url:
            self.radiobutton_register.hide()
        if small_icon:
            self.window.set_icon_name(small_icon)
        if large_icon:
            self.image_logo.set_from_pixbuf(icontheme.load_icon(large_icon, 48, ( )))
        
        text = _("To upload a screencast to %s, you need a %s account.") % (name, name)
        self.label_primary.set_text('<span font_size="large">%s</span>' % text)
        self.label_primary.set_use_markup(True)
        self.label_primary.set_line_wrap(True)
        self.radiobutton_has_account.set_label(_('I have a %s account:') % name)
        
    def on_button_cancel_clicked(self, button):
        self.action = self.ACTION_CANCEL
        self.window.destroy()
        
    def on_button_continue_clicked(self, button):
        if self.action == self.ACTION_LOGIN:
            username = self.entry_username.get_text()
            password = self.entry_password .get_text()
            self.details = (username, password)
            self.window.destroy()
        elif self.action == self.ACTION_REGISTER:
            webbrowser.open(self.register_url)
            gobject.timeout_add(5000, self.focus_login)
        
    def on_radiobutton_toggled(self, radiobutton):
        if not radiobutton.get_active():
            return # Ignore the just untoggled radiobutton
            
        radiobutton_group = radiobutton.get_group()
        # They are reversed for some reason
        radiobutton_group.reverse()
        index = radiobutton_group.index(radiobutton)
        # Find where the radiobutton is in the window..
        # and set the action appropriately
        self.action = index
        
        # Make the widgets under the first radiobutton 
        # insensitive if appropriate
        for widget in [self.label_username, 
                        self.entry_username, 
                        self.label_password, 
                        self.entry_password]:
            widget.set_sensitive(index == self.ACTION_LOGIN)
    
    def focus_login(self):
        self.radiobutton_has_account.set_active(True)
        self.entry_username.grab_focus()
        return False
        
    def run(self):
        self.window.show_all()

if __name__ == "__main__":
    if os.path.exists("./data/ui/authenticate.ui"):
        logging.info("Running locally")
        datadir = "./data"
    else:
        datadir = "/usr/share/kazam/"

    icons = gtk.icon_theme_get_default()
    icons.append_search_path(os.path.join(datadir,"icons", "48x48", "apps"))
    icons.append_search_path(os.path.join(datadir,"icons", "16x16", "apps"))
    name = "YouTube"
    icon = ("youtube", "youtube")
    register_url = "http://www.google.com"
    
    authenticate_dialog = AuthenticateDialog(datadir, name, icons, icon, register_url)
    authenticate_dialog.run()
    gtk.main()
    
    """dialog = new_linkbutton_dialog("http://www.google.com", 
            _("Your screencast has uploaded successfully."),
            _("It is available at the location below:"))"""
