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

# Based from youtube-upload by Arnau Sanchez <tokland@gmail.com>

import urllib2
import gobject

# python-gdata (>= 1.2.4)
import gdata.media
import gdata.geo
import gdata.youtube
import gdata.youtube.service

from upload_source import UploadSource

from xml.etree import ElementTree

class YouTube(UploadSource):
    """Interface the Youtube API."""        

    DEVELOPER_KEY = "AI39si4K_qwy_KQ5HHNXYF9so0mBiKqMJnZ7gJVs3jW9nSKOcPfhTl" + \
                    "aFw8_jIaDvZyRLrmwa0X8eOjsfg3lHyQdsfmah7ja7Rw"
    CATEGORIES_SCHEME = "http://gdata.youtube.com/schemas/2007/categories.cat"

    META = {
            "title":"entry_title",
            "keywords":"entry_keywords",
            "description":"textview_description",
            #"category":"",
            }

    def __init__(self):
        super(YouTube, self).__init__()
        self.service = gdata.youtube.service.YouTubeService()
                
        self.categories = self._get_categories_dict()
        self.video_entry = None
        
    def authenticate(self, email, password):
        self.service.ssl = False # SSL is not yet supported by Youtube API
        self.service.email = email
        self.service.password = password
        self.service.developer_key = self.DEVELOPER_KEY
        try:
            self.service.ProgrammaticLogin()
            return True
        except:
            return False

    def upload(self, path):
        entry = self.service.InsertVideoEntry(self.video_entry, path)
        url = entry.GetHtmlLink().href
        url = url.replace("&feature=youtube_gdata", "")
        self.emit("upload-complete", url)
           
    def create_meta(self, title, description, category_term, keywords=None, private=False):
        if not self._check_category(category_term):
            print "Not suitable"
            return False
        # Create all meta objects
        meta_title = gdata.media.Title(text=title)
        meta_description = gdata.media.Description(description_type='plain',
                                                    text=description)
        meta_keywords = gdata.media.Keywords(text=keywords)
        meta_category = gdata.media.Category(text=category_term,
                                        label=self.categories[category_term]["label"],
                                        scheme=self.CATEGORIES_SCHEME)
        if private:
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
       
    def _check_category(self, category_term):
        """
        Checks whether a given category is acceptable, return True if
        it is, False if it isn't
        """
        return category_term in self.categories
            
    def _get_categories_dict(self):
        """
        {
        "Film":{
                "label":"Film & Animation",
                "depreciated":False,
                }
        }
        """
        category_dict = {}
        
        tree = ElementTree.parse("/tmp/categories.cat")
        categories = tree.getroot()
        for category in categories.getchildren():
            term = category.get("term")
            label = category.get("label")
            if category.find("{http://gdata.youtube.com/schemas/2007}assignable") == None:
                depreciated = True
            else:
                depreciated = False
            category_dict[term] = {"label":label, "depreciated":depreciated}
            
        return category_dict
