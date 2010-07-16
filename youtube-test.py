#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       untitled.py
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

# Uses code from youtube-upload by Arnau Sanchez <tokland@gmail.com>

import os
import sys
import locale
import urllib
import optparse
import itertools
import subprocess
from xml.etree import ElementTree

# python-gdata (>= 1.2.4)
import gdata.media
import gdata.geo
import gdata.youtube
import gdata.youtube.service

VERSION = "0.4"
DEVELOPER_KEY = "AI39si7iJ5TSVP3U_j4g3GGNZeI6uJl6oPLMxiyMst24zo1FEgnLzcG4i" + \
                "SE0t2pLvi-O03cW918xz9JFaf_Hn-XwRTTK7i1Img"

class Youtube:
    """Interface the Youtube API."""        
    CATEGORIES_SCHEME = "http://gdata.youtube.com/schemas/2007/categories.cat"
    
    def __init__(self, developer_key, email, password, source=None, client_id=None):
        """Login and preload available categories."""
        service = gdata.youtube.service.YouTubeService()
        service.ssl = False # SSL is not yet supported by Youtube API
        service.email = email
        service.password = password
        service.source = source
        service.developer_key = developer_key
        service.client_id = client_id
        service.ProgrammaticLogin()
        self.service = service
        self.categories = self.get_categories()

    def get_upload_form_data(self, path, *args, **kwargs):
        """Return dict with keys 'post_url' and 'token' with upload info."""
        video_entry = self._create_video_entry(*args, **kwargs)
        post_url, token = self.service.GetFormUploadToken(video_entry)
        debug("post url='%s', token='%s'" % (post_url, token))
        return dict(post_url=post_url, token=token)

    def upload_video(self, path, *args, **kwargs):
        """Upload a video."""
        video_entry = self._create_video_entry(*args, **kwargs)
        return self.service.InsertVideoEntry(video_entry, path)

    def upload_video_to_playlist(self, video_id, playlist_uri, title=None, description=None):
        """Add video to playlist."""
        playlist_video_entry = self.service.AddPlaylistVideoEntryToPlaylist(
            playlist_uri, video_id, title, description)
        return playlist_video_entry
           
    def _create_video_entry(self, title, description, category, keywords=None, 
            location=None, private=False):
        assert self.service, "Youtube service object is not set"
        if category not in self.categories:
            valid = " ".join(self.categories.keys())
            raise ValueError("Invalid category '%s' (valid: %s)" % (category, valid))
                 
        media_group = gdata.media.Group(
            title=gdata.media.Title(text=title),
            description=gdata.media.Description(description_type='plain', text=description),
            keywords=gdata.media.Keywords(text=", ".join(keywords or [])),
            category=gdata.media.Category(
                text=category,
                label=self.categories[category],
                scheme=self.CATEGORIES_SCHEME),
            private=(gdata.media.Private() if private else None),
            player=None)
        if location:            
            where = gdata.geo.Where()
            where.set_location(location)
        else: 
            where = None
        return gdata.youtube.YouTubeVideoEntry(media=media_group, geo=where)
                
    @classmethod
    def get_categories(cls):
        """Return categories dictionary with pairs (term, label)."""
        def get_pair(element):
            """Return pair (term, label) for a (non-deprecated) XML element."""
            if all(not(str(x.tag).endswith("deprecated")) for x in element.getchildren()):
                return (element.get("term"), element.get("label"))            
        xmldata = urllib.urlopen(cls.CATEGORIES_SCHEME).read()
        xml = ElementTree.XML(xmldata)
        return dict(filter(bool, map(get_pair, xml)))
    
def main_upload(arguments):
    """Upload video to Youtube."""
    usage = """Usage: %prog [OPTIONS] EMAIL PASSWORD FILE TITLE DESCRIPTION CATEGORY KEYWORDS"""
    
    print " ".join(Youtube.get_categories().keys())
    
    encoding = get_encoding()
    email, password0, video_path, title, description, category, skeywords = \
        [unicode(s, encoding) for s in args]
    password = (sys.stdin.readline().strip() if password0 == "-" else password0)
    videos = ([video_path] if options.no_split else list(split_youtube_video(video_path)))
    debug("connecting to Youtube API")
    yt = Youtube(DEVELOPER_KEY, email, password)
    keywords = filter(bool, [s.strip() for s in re.split('[,;\s]+', skeywords)])
    
    
    for index, splitted_video_path in enumerate(videos):
        complete_title = ("%s [%d/%d]" % (title, index+1, len(videos)) 
                          if len(videos) > 1 else title)
        args = [splitted_video_path, complete_title, description, category, keywords]
        kwargs = dict(private=options.private, location=parse_location(options.location))
        if options.get_upload_form_data:
          data = yt.get_upload_form_data(*args, **kwargs)
          print "|".join([splitted_video_path, data["token"], data["post_url"]])
          if options.playlist_uri:
              debug("--playlist-uri is ignored on form upload")        
        else:
          debug("start upload: %s (%s)" % (splitted_video_path, complete_title)) 
          entry = yt.upload_video(*args, **kwargs)
          url = entry.GetHtmlLink().href.replace("&feature=youtube_gdata", "")
          print url

   
if __name__ == '__main__':
    sys.exit(main_upload(sys.argv[1:]))

