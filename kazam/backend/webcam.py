# -*- coding: utf-8 -*-
#
#       webcam.py
#
#       Copyright 2014 David Klasinc <bigwhale@lubica.net>
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
import glob
import logging

from gi.repository import GObject, GUdev

logger = logging.getLogger("Webcam")


class Webcam(GObject.GObject):

    """docstring for Webcam."""

    def __init__(self):
        super(Webcam, self).__init__()

        self.device_list = []
        self.has_webcam = False

        logger.debug("Initializing webcam support.")
        self.udev_client = GUdev.Client.new(subsystems=['video4linux'])
        self.udev_client.connect("uevent", self.watch)
        self.detect()

    def watch(self, client, action, device):
        print(action)
        for device_key in device.get_property_keys():
            print ("device property {}: {}".format(device_key, device.get_property(device_key)))
        print("\n\n")

    def detect(self):
        if os.path.isdir("/sys/class/video4linux"):
            logger.debug("Video for linux supported.")
            files = glob.glob("/sys/class/video4linux/*")
            for f in files:
                with open(f + "/index", "r") as r:
                    cam_index = r.read().strip()
                with open(f + "/dev", "r") as r:
                    cam_dev_id = r.read().strip()
                with open(f + "/name", "r") as r:
                    cam_name = r.read().strip()
                cam_dev = "/dev/" + os.path.basename(f)
                logger.debug("  Webcam found: {0}".format(cam_name))
                self.device_list.append([int(cam_index), cam_dev_id, cam_dev, cam_name])
        else:
            logger.warning("Video for linux not supported.")

        if self.device_list:
            self.has_webcam = True

        return self.device_list

    def get_device_file(self, num):
        try:
            return self.device_list[num][2]
        except:
            return None
