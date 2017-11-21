#! /usr/bin/env python
# -*- coding: utf-8 -*-

import daiquiri
from time import time
import warp10client

LOG = daiquiri.getLogger(__name__)

warp10_api_url = ''  # Add here backend url where metrics are stored
read_token = ''  # Add here your metrics read token
write_token = ''  # Add here your metrics write token

# To get metrics:
metric_get = {
    'name': 'cpu_util',
    'tags': {
        'resource_id': '18d94676-077c-4c13-b000-27fd603f3056',
        'project_id': '8069f876e7d444249ef04b9a74090711',
    },
    'aggregate': {
        'type': 'mean',
        'span': 1000000 * 3600,
    },
    'timestamp': {
        'start': "2017-01-01T00:00:00.000Z",
        'end': "2018-01-01T00:00:00.000Z"
    }
    # 'timestamp': { 'end': "2018-01-01T00:00:00.000Z" }
    # 'timestamp': { 'start': None, 'end': None }
}

# To write metrics:
metric_write = {
    'name': 'cpu_util_mjozefcz',
    'tags': {
        'resource_id': '18d94676-077c-4c13-b000-27fd603f3056',
        'project_id': '8069f876e7d444249ef04b9a74090711',
        'unit': '%',
    },
    'position': {
        'longitude': None,
        'latitude': None,
        'elevation': None,
        'timestamp': time() * 1000 * 1000,
    },
    'value': 11,
}

# To check metrics
metric_check = {
    'name': 'cpu_util',
    'tags': {
        'resource_id': '18d94676-077c-4c13-b000-27fd603f3056',
        'project_id': '8069f876e7d444249ef04b9a74090711',
    },
}

# arguments need to authorize in metrics backend
kwargs = {
    'write_token': write_token,
    'read_token': read_token,
    'warp10_api_url': warp10_api_url,
}

client = warp10client.Warp10Client(**kwargs)

# Consider to create timeseries, new object with included metrics as each point
# Thats goooood idea.
metric_get_test = client.get(metric_get)

metric_exists = client.exists(metric_check)

metric_obj = warp10client.Metric(**metric_write)

metric_send = client.set(metric_write)

# delete method is not yet implemented
# metric_send = client.delete(metric_write)
