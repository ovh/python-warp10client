#!/usr/bin/env python
# -*- coding: utf-8 -*-

from time import time


class Position(object):
    def __init__(self, timestamp=time(), latitude=None, longitude=None,
                 elevation=None):
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        self.timestamp = timestamp
