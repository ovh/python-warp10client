#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from urllib.parse import quote_plus
except ImportError:
    from urllib import quote_plus

from time import time

from warp10client.position import Position


class Metric(object):
    # NOTE(mjozefcz): Consider to add here maybe some extra if needed?
    DEFAULT_TAGS = {
        # 'host': gethostname() # DO NOT CREATE SILOS, what if vm has
        # been migrated to other host?! hah...
    }

    DEFAULT_LOCATION = {
        'latitude': None,
        'longitude': None,
    }

    def __init__(self, name, value=None, tags=None, position=None):
        self.name = name
        self.value = value
        self._tags = Metric.DEFAULT_TAGS.copy()
        self._tags.update(**tags)
        self.position = self._fill_current_position(position=position)

    def __repr__(self):
        tags = list(self._tags.keys())
        if tags:
            tags.sort()
            tags = ' ' + (' '.join(
                '{}={}'.format(k, self._tags[k])
                for k in tags
            ))

        return '<Metric {} value={} timestamp={} ' \
               'lat_lon={} elevation={} {}>'.format(quote_plus(self.name),
                                                    self.value,
                                                    self.position.timestamp,
                                                    self.position.lat_lon,
                                                    self.position.elevation,
                                                    tags or '')

    def format_metric(self):
        tags = ','.join(
            '{}={}'.format(quote_plus(k), quote_plus(self._tags[k]))
            for k in self._tags if self._tags[k]
        )
        metric_name = quote_plus(self.name)
        if type(self.value) == bool:
            metric_value = 'T' if self.value else 'F'
        elif type(self.value) == str:
            metric_value = "'{}'".format(quote_plus(self.value))
        else:
            metric_value = self.value
        return '{}/{}/{} {}{} {}'.format(
            int(self.position.timestamp),
            self.position.lat_lon,
            self.position.elevation,
            metric_name, '{' + tags + '}', metric_value)

    def _fill_current_position(self, position):
        if position is None:
            position = Position(
                time(),
                **Metric.DEFAULT_LOCATION
            )
        elif not isinstance(position, Position):
            kwargs = Metric.DEFAULT_LOCATION
            kwargs.update(position)
            position = Position(**kwargs)

        def xstr(s):
            return '' if s is None else str(s)

        if position.latitude or position.longitude:
            position.lat_lon = '{}:{}'.format(xstr(position.latitude),
                                              xstr(position.longitude))
        else:
            position.lat_lon = ''
        position.elevation = '' \
            if position.elevation is None \
            else int(position.elevation)

        return position
