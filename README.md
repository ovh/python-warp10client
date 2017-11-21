Python Warp10 Client
====================

This repository contains simple python client for Warp10 metric
engine.


Examples:

Create client object
--------------------
```
kwargs = {
    'write_token': write_token,
    'read_token': read_token,
    'warp10_api_url': warp10_api_url,
}

import warp10client
client = warp10client.Warp10Client(**kwargs)
```

Send metric
-----------
To write metrics (one or multiple at same time)
```
metric_write = [
{
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
]

metric_send = client.set(metric_write)
metric_send
[<Metric cpu_util_mjozefcz value=11 timestamp=1.50660126016e+15 lat_lon= elevation=  project_id=8069f876e7d444249ef04b9a74090711 resource_id=18d94676-077c-4c13-b000-27fd603f3056 unit=%>]
```

Get metric
----------
```
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
    'timestamp': { 'start': "2017-01-01T00:00:00.000Z", 'end': "2018-01-01T00:00:00.000Z" }
    #'timestamp': { 'end': "2018-01-01T00:00:00.000Z" }
    #'timestamp': { 'start': None, 'end': None }
}
metric_get_test = client.get(metric_get)
metric_get_test
<warp10client.timeserie.Timeserie object at 0x7f3e144baf90>
```

Check metric
------------
```
metric_check= {
    'name': 'cpu_util',
    'tags': {
              'resource_id': '18d94676-077c-4c13-b000-27fd603f3056',
              'project_id': '8069f876e7d444249ef04b9a74090711',
             },
}
metric_exists = client.exists(metric_check)
metric_exists
True
```

Delete metric
-------------
TDB
