# -*- coding: utf-8 -*-
#
#       youtube.py
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

# Thankyou to youtube-upload (by Arnau Sanchez) for helping me to understand this =)

import os
# import gtk
# import gobject
from urllib import urlopen
from threading import Thread
from xml.etree import ElementTree

# python-gdata (>= 1.2.4)
import gdata.media
import gdata.geo
import gdata.youtube
import gdata.youtube.service

from kazam.backend.export_sources import UploadSuperSource
#from kazam.frontend.widgets.comboboxes import EasyTextComboBox, EasyTextAndObjectComboBox
from kazam.utils import setup_ui

class UploadSource(UploadSuperSource):
    """Interface the Youtube API."""

    ICONS = ("youtube", "youtube")
    NAME = "YouTube"
    REGISTER_URL = "http://www.youtube.com/create_account"
    CATEGORIES_SCHEME_URL = "http://gdata.youtube.com/schemas/2007/categories.cat"

    DEVELOPER_KEY = "AI39si4K_qwy_KQ5HHNXYF9so0mBiKqMJnZ7gJVs3jW9nSKOcPfhTl" + \
                    "aFw8_jIaDvZyRLrmwa0X8eOjsfg3lHyQdsfmah7ja7Rw"

    META = {
            "title":"entry_title",
            "keywords":"entry_keywords",
            "description":"textview_description",
            "category":"combobox_category",
            "private":"combobox_private",
            }

    FFMPEG_OPTIONS = []
    FFMPEG_FILE_EXTENSION = ".mp4"

    def __init__(self):
        super(UploadSource, self).__init__()
        self.authentication = True
        self.service = gdata.youtube.service.YouTubeService()

        self.video_entry = None
        self.entry = None

    ###

    def login_pre(self, username, password):
        self.service.ssl = False # SSL not yet supported by Youtube API
        self.service.email = username
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

    def create_meta(self, title, description, category, keywords, private):
        (category_label, category_term) = category

        if private == "True":
            meta_private = gdata.media.Private()
        else:
            meta_private = None

        # Create all meta objects
        meta_title = gdata.media.Title(text=title)
        meta_description = gdata.media.Description(description_type='plain',
                                                    text=description)
        meta_keywords = gdata.media.Keywords(text=keywords)
        meta_category = gdata.media.Category(text=category_term,
                                        label=category_label,
                                        scheme=self.CATEGORIES_SCHEME_URL)

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

    def _get_categories_dict(self):
        """
        {
        "Film":{
                "label":"Film & Animation",
                "depreciated":False,
                }
        }
        """

        # Parse the XML and put it into a dictionary
        category_dict = {}
        tree = ElementTree.fromstring(CATEGORIES_SCHEME)
        categories = tree
        for category in categories.getchildren():
            term = category.get("term")
            label = category.get("label")
            # Check whether it is depreciated or not
            if category.find("{http://gdata.youtube.com/schemas/2007}assignable") == None:
                depreciated = True
            else:
                depreciated = False
            category_dict[term] = {"label":label, "depreciated":depreciated}

        self.categories = category_dict

    def gui_extra(self, datadir):
        setup_ui(self, os.path.join(datadir, "ui", "export_sources", "youtube.ui"))

        self.combobox_category = EasyTextAndObjectComboBox()
        liststore_category = self.combobox_category.get_model()
        self.combobox_private = EasyTextComboBox()

        # Get our categories file and parse it into combobox_category
        self._get_categories_dict()
        for category in self.categories:
            category_term = self.categories[category]
            category_label = category_term["label"]
            if not category_term["depreciated"]:
                liststore_category.append([category_label, category])

        for state in ["False", "True"]:
            self.combobox_private.get_model().append([state])

        self.table_properties.attach(self.combobox_category, 1, 2, 3, 4,
                                    (gtk.FILL), ( ), xpadding=6)
        self.combobox_category.set_active(0)
        self.combobox_category.show()

        self.table_properties.attach(self.combobox_private, 1, 2, 5, 6,
                                    (gtk.FILL), ( ), xpadding=6)
        self.combobox_private.set_active(0)
        self.combobox_private.show()

    def property_alignment_expose(self):
        self.combobox_category.set_active(0)


CATEGORIES_SCHEME = """<?xml version='1.0' encoding='UTF-8'?><app:categories xmlns:app='http://www.w3.org/2007/app' xmlns:atom='http://www.w3.org/2005/Atom' xmlns:yt='http://gdata.youtube.com/schemas/2007' fixed='yes' scheme='http://gdata.youtube.com/schemas/2007/categories.cat'><atom:category term='Film' label='Film &amp; Animation' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Autos' label='Cars &amp; Vehicles' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Music' label='Music' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Animals' label='Pets &amp; Animals' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Sports' label='Sport' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Travel' label='Travel &amp; Events' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Shortmov' label='Short Films' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Videoblog' label='Videoblogging' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Games' label='Gaming' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Comedy' label='Comedy' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='People' label='People &amp; Blogs' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='News' label='News &amp; Politics' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Entertainment' label='Entertainment' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Education' label='Education' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Howto' label='Howto &amp; Style' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Nonprofit' label='Non-profits &amp; Activism' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='US'/></atom:category><atom:category term='Tech' label='Science &amp; Technology' xml:lang='en-GB'><yt:assignable/><yt:browsable regions='AR AU BR CA CZ DE DK ES FI FR GB GR HK HR HU IE IL IN IT JP KR MX NL NO NZ PL PT RU SE SK SR TW US ZA'/></atom:category><atom:category term='Movies_Anime_animation' label='Films - Anime/Animation' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies' label='Films' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies_Comedy' label='Films - Comedy' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies_Documentary' label='Films - Documentary' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies_Action_adventure' label='Films - Action/Adventure' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies_Classics' label='Films - Classics' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies_Foreign' label='Films - Foreign' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies_Horror' label='Films - Horror' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies_Drama' label='Films - Drama' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies_Family' label='Films - Family' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies_Shorts' label='Films - Shorts' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Shows' label='Shows' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies_Sci_fi_fantasy' label='Films - Sci-Fi/Fantasy' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Movies_Thriller' label='Films - Thriller' xml:lang='en-GB'><yt:deprecated/></atom:category><atom:category term='Trailers' label='Trailers' xml:lang='en-GB'><yt:deprecated/></atom:category></app:categories>"""
