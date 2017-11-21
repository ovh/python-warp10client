#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Timeserie(object):
    def __init__(self, start=None, stop=None, metrics=[],
                 aggregation=None, granularity=None):
        self.start = start
        self.stop = stop
        self.metrics = metrics
        self.aggregation = aggregation
        self.granularity = granularity
