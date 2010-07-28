#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       youtube.py
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

# Thankyou to youtube-upload (by Arnau Sanchez) for making this simpler =)

import gtk
import gobject
from urllib import urlopen
from threading import Thread
from xml.etree import ElementTree

# python-gdata (>= 1.2.4)
import gdata.media
import gdata.geo
import gdata.youtube
import gdata.youtube.service

from upload_source import UploadSource
from kazam.widgets.comboboxes import EasyTextComboBox

class YouTube(UploadSource):
    """Interface the Youtube API."""        

    ICONS = ("youtube", "youtube")
    NAME = "YouTube"
    REGISTER_URL = "http://www.youtube.com/create_account"

    DEVELOPER_KEY = "AI39si4K_qwy_KQ5HHNXYF9so0mBiKqMJnZ7gJVs3jW9nSKOcPfhTl" + \
                    "aFw8_jIaDvZyRLrmwa0X8eOjsfg3lHyQdsfmah7ja7Rw"
    CATEGORIES_SCHEME = "http://gdata.youtube.com/schemas/2007/categories.cat"

    META = {
            "title":"entry_title",
            "keywords":"entry_keywords",
            "description":"textview_description",
            "category_term":"combobox_category",
            "private":"combobox_private",
            }

    def __init__(self):
        super(YouTube, self).__init__()
        self.authentication = True
        self.service = gdata.youtube.service.YouTubeService()
                
        self.categories = self._get_categories_dict()
        self.video_entry = None
        self.entry = None
       
    ###
    
    def login_pre(self, email, password):
        self.service.ssl = False # SSL not yet supported by Youtube API
        self.service.email = email
        self.service.password = password
        self.service.developer_key = self.DEVELOPER_KEY
        
    def login_in(self):
        self.service.ProgrammaticLogin()
        
    def login_post(self):
        pass
        
    ###
        
    def upload_pre(self):
        pass
        
    def upload_in(self, path):
        self.entry = self.service.InsertVideoEntry(self.video_entry, path)
        
    def upload_post(self):
        url = self.entry.GetHtmlLink().href
        url = url.replace("&feature=youtube_gdata", "")
        return url

    ###
           
    def create_meta(self, title, description, category_term, keywords=None, private=False):
        # Create all meta objects
        meta_title = gdata.media.Title(text=title)
        meta_description = gdata.media.Description(description_type='plain',
                                                    text=description)
        meta_keywords = gdata.media.Keywords(text=keywords)
        meta_category = gdata.media.Category(text=category_term,
                                        label=self.categories[category_term]["label"],
                                        scheme=self.CATEGORIES_SCHEME)
        if private == "True":
            meta_private = gdata.media.Private()
        else:
            meta_private = None   
             
        # Put them in our media group
        media_group = gdata.media.Group(
            title=meta_title,
            description=meta_description,
            keywords=meta_keywords,
            category=meta_category,
            private=meta_private,
            player=None)

        # Create a VideoEntry
        self.video_entry = gdata.youtube.YouTubeVideoEntry(media=media_group)
        return True
            
    def _get_categories_dict(self):
        """
        {
        "Film":{
                "label":"Film & Animation",
                "depreciated":False,
                }
        }
        """
        # Download the Categories XML file from Youtube in a thread
        thread = Thread(target=self._download_categories_thread)
        thread.start()
        # Wait till it is done
        while thread.isAlive():
            gtk.main_iteration()
            
        # Parse the XML and put it into a dictionary
        category_dict = {}
        tree = ElementTree.parse(self.categories_file)
        self.categories_file.close()
        categories = tree.getroot()
        for category in categories.getchildren():
            term = category.get("term")
            label = category.get("label")
            # Check whether it is depreciated or not
            if category.find("{http://gdata.youtube.com/schemas/2007}assignable") == None:
                depreciated = True
            else:
                depreciated = False
            category_dict[term] = {"label":label, "depreciated":depreciated}
            
        return category_dict
        
    def _download_categories_thread(self):
        self.categories_file = urlopen(self.CATEGORIES_SCHEME)

        
def YouTube_extra_gui(self, youtube_class, alignment):
    self.combobox_category = EasyTextComboBox()
    self.combobox_private = EasyTextComboBox()
        
    categories = youtube_class().categories.copy()
    for category in categories:
        if not categories[category]["depreciated"]:
            self.combobox_category.get_model().append([categories[category]["label"]])
            
    for state in ["False", "True"]:
        self.combobox_private.get_model().append([state])
                
    self.table_youtube.attach(self.combobox_category, 1, 2, 3, 4, ( ), ( ))
    self.combobox_category.set_active(0)
    self.combobox_category.show()    
    
    self.table_youtube.attach(self.combobox_private, 1, 2, 5, 6, ( ), ( ))
    self.combobox_private.set_active(0)
    self.combobox_private.show()
    
