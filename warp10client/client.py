#!/usr/bin/env python
# -*- coding: utf-8 -*-

import hashlib
import re

from copy import deepcopy
from functools import wraps

import daiquiri
import requests
import six

from warp10client.common import constants
from warp10client.metric import Metric
from warp10client.position import Position
from warp10client.timeserie import Timeserie

# TODO(mjozefcz):
# Consider multithread for all functions

LOG = daiquiri.getLogger(__name__)


class Warp10Client(object):
    # TODO(mjozefcz):
    # Check those methods:
    # * 'std'
    # * 'rate:.*'
    # If those bucketizers exists in Warp10

    VALID_AGGREGATION_METHODS = {
        'mean', 'sum', 'last', 'max', 'min', 'median', 'first', 'count'
    }.union(
        set(
            (str(i) + 'pct' for i in six.moves.range(1, 100))
        )
    )

    AGGREGATION_METHODS_MAP = dict(
        (key, 'percentile') for key in set(
            (str(i) + 'pct' for i in six.moves.range(1, 100))
        )
    )

    CALL_RESP_STATUS = {
        'fetch': 200,
        'ingress': 200,
        'delete': 200,
    }

    def check_resp_status():
        def decorate(func):
            def newfunc(*arg, **kw):
                out = func(*arg, **kw)
                expected_code = Warp10Client.CALL_RESP_STATUS.get(
                    kw.get('call_type'))
                if not out.status_code == expected_code:
                    raise requests.RequestException(
                        'Warp10 API answered with not expected '
                        'HTTP status code - returned: '
                        '%(returned)s expected: %(expected)s, '
                        'reason: %(reason)s' %
                        {'expected': expected_code,
                         'returned': out.status_code,
                         'reason': out.reason})
                else:
                    return out
            newfunc = wraps(func)(newfunc)
            return newfunc
        return decorate

    def __init__(self, read_token=None, write_token=None,
                 warp10_api_url=None, tags=None):
        self._session = requests.Session()
        self._read_token = read_token
        self._write_token = write_token
        self._warp10_api_url = warp10_api_url
        self._tags = tags

    def _get_token(self, call_type='fetch'):
        if call_type in ('delete', 'ingress'):
            return self._write_token
        else:
            return self._read_token

    def _get_headers(self, call_type='fetch'):
        headers = dict()
        headers[constants.WARP_TOKEN_HEADER_NAME] = \
            self._get_token(call_type=call_type)
        if call_type == 'ingress':
            headers['Content-Type'] = 'text/plain'
        return headers

    @staticmethod
    def _get_method(call_type='fetch'):
        if call_type in ('fetch', 'ingress'):
            return 'POST'
        else:
            return 'GET'

    def _get_url(self, call_type='fetch'):
        if call_type == 'fetch':
            api_endpoint = 'exec'
        elif call_type == 'ingress':
            api_endpoint = 'update'
        else:
            api_endpoint = 'delete'
        return "%s/%s" % (self._warp10_api_url, api_endpoint)

    @staticmethod
    def _get_aggregation_method(method):
        if method in Warp10Client.AGGREGATION_METHODS_MAP.keys() and \
                method in Warp10Client.VALID_AGGREGATION_METHODS:
            return Warp10Client.AGGREGATION_METHODS_MAP.get(method)
        elif method in Warp10Client.VALID_AGGREGATION_METHODS:
            return method
        else:
            raise NotImplementedError('Aggregation method %s is not '
                                      'valid aggregation' %
                                      method)

    @staticmethod
    def _get_aggregation_parameter(method):
        args = re.search('([0-9]+)[a-z]+', method)
        if method in Warp10Client.AGGREGATION_METHODS_MAP.keys() and \
                len(args.groups()) > 0:
            # NOTE(mjozefcz): Don't ask me why it should be mapped
            # to float. Warp10...
            return float(args.group(1))
        return ''

    def send_request(self, headers, data):
        result = self._session.post(self._warp10_api_url,
                                    headers=headers,
                                    data=data)
        return result

    def exists(self, metric):
        """

        Check if metric exists in Warp10 backend.

        :param metric: Hash with metric that needs to be checked
        :return: bolean

        """
        return len(self.get(metric).metrics) > 0

    def get(self, metric):
        """

        Get metric from Warp10

        :param metric: Hash with metric that needs to be fetched
        :return timeserie: timeserie object

        """
        resp = self._call(metric, call_type='fetch')
        metric_list = list()
        if eval(resp.content)[0]:
            values = eval(resp.content)[0][0].get('v')
            name = eval(resp.content)[0][0].get('c')
            tags = eval(resp.content)[0][0].get('l')
            timestamps = [v[0] for v in values]
            start = min(timestamps)
            stop = max(timestamps)
            for value in values:
                metric_list.append(
                    Metric(name=name,
                           value=value[1],
                           tags=tags,
                           position=Position(timestamp=value[0])))
            timeserie = Timeserie(start=start, stop=stop,
                                  metrics=metric_list)
            return timeserie
        else:
            return Timeserie()

    def set(self, metrics):
        """

        Send metrics to WARP10 backend.

        :param metrics: Hash with metric or list of metrics Hashes
        :return added_metrics: list of metric objects

        """
        metrics = [metrics] if type(metrics) == dict else metrics
        added_metrics = list()
        self._call(metrics, call_type='ingress')
        for metric in metrics:
            added_metrics.append(
                Metric(name=metric.get('name'),
                       value=metric.get('value'),
                       tags=metric.get('tags'),
                       position=Position(**metric.get('position'))))
        return added_metrics

    def delete(self, metrics):
        """

        Delete metrics from WARP10 backend.

        :param metrics: Hash with metric or list of metrics Hashes
        :return bolean

        """
        raise NotImplementedError

    @staticmethod
    def _remove_sensitive_data(data):
        # NOTE(danpawlik) Remove sensitive data like: Warp10token.
        if constants.WARP_TOKEN_HEADER_NAME in data:
            data[constants.WARP_TOKEN_HEADER_NAME] = (hashlib.sha256(
                data[constants.WARP_TOKEN_HEADER_NAME]).hexdigest()
            )
        return data

    @check_resp_status()
    def _call(self, metrics, call_type='fetch'):
        url = self._get_url(call_type=call_type)
        headers = self._get_headers(call_type=call_type)

        try:
            data = self._gen_request_body(metrics=metrics,
                                          call_type=call_type)
        except Exception as e:
            raise Exception('Failed to prepare request.\n'
                            'Error: %s\n'
                            'Endpoint: %s\n'
                            'Headers: %s'
                            % (e.message, url,
                               self._remove_sensitive_data(
                                   deepcopy(headers))))

        LOG.debug('Calling API with parameters: \n'
                  'url: %(url)s \n'
                  'headers: %(headers)s \n'
                  'data: %(data)s',
                  {'url': url,
                   'headers': self._remove_sensitive_data(deepcopy(headers)),
                   'data': self._remove_sensitive_data(deepcopy(data))})

        try:
            return getattr(self._session,
                           self._get_method(call_type=call_type).lower())(
                url,
                headers=headers,
                data=data)
        except Exception as e:
            raise Exception('Failed to gather data from WARP10 endpoint.\n'
                            'Error: %s\n'
                            'Endpoint: %s\n'
                            'Headers: %s\n'
                            'Data: %s'
                            % (e.message, url,
                               self._remove_sensitive_data(deepcopy(headers)),
                               self._remove_sensitive_data(deepcopy(data))))

    def _gen_request_body(self, metrics, call_type='fetch'):
        if call_type == 'fetch':
            return self._gen_warp10_script(metrics)
        elif call_type == 'ingress':
            return self._get_write_body(metrics)
        else:
            return self._get_delete_body(metrics)

    def _gen_warp10_script_timebound(self, metric):
        t_h = metric.get('timestamp', None)
        w_s = str()
        if t_h:
            if t_h.get('start') and t_h.get('end'):
                w_s = "'{}' '{}'".format(t_h.get('start'),
                                         t_h.get('end'))
            elif t_h.get('start'):
                w_s = "'{}' {}".format(t_h.get('start'),
                                       'NOW ISO8601')
            elif t_h.get('end'):
                w_s = "'{}' '{}'".format('1970-01-01T01:01:00.000Z',
                                         t_h.get('end'))
            else:
                # NOTE(mjozefcz): In this case get all metrics
                w_s = "'1970-01-01T01:01:00.000Z' NOW ISO8601"
        else:
            # NOTE(mjozefcz): In this case get all metrics
            w_s = "'1970-01-01T01:01:00.000Z' NOW ISO8601"
        return w_s

    def _get_warp10_script_aggregation(self, metric):
        w_s = str()
        if metric.get('aggregate', None):
            aggregate = metric.get('aggregate')

            aggregate_type = aggregate.get('type', None)
            if aggregate_type:
                method = self._get_aggregation_method(aggregate_type)
                param = self._get_aggregation_parameter(aggregate_type)
            else:
                method = 'mean'
                param = ''

            aggregate_span = aggregate.get('span', None)
            if aggregate_span:
                span = int(aggregate_span)
            else:
                span = 1000000

            w_s = '[ SWAP {} bucketizer.{} 0 {} 0 ] BUCKETIZE'.format(
                param, method.lower(), span)
        return w_s

    def _get_warp10_script_tags(self, metric):
        w_s = str()
        if metric.get('tags', None):
            tags = metric.get('tags')
            # Cook string like "{ 'key1' 'value' 'key2' 'value2' ...}"
            w_s = '{{ {} }}'.format(' '.join("'%s' '%s'" %
                                    (t_k, t_v) for t_k, t_v in
                six.iteritems(tags) if t_v))
        return w_s

    def _gen_warp10_script(self, metric):
        return "[ '{}' '{}' {} {} ] FETCH {} ".format(
            self._get_token(),
            metric.get('name'),
            self._get_warp10_script_tags(metric),
            self._gen_warp10_script_timebound(metric),
            self._get_warp10_script_aggregation(metric)
        )

    def _get_write_body(self, metrics):
        metrics = self._convert_metrics(
            [metrics] if type(metrics) == dict else metrics
        )
        data = str()
        for metric in metrics:
            data += '{}\n'.format(metric.format_metric())
        return data

    def _get_delete_body(self, metrics):
        return str()

    def _convert_metrics(self, metrics):
        data = list()
        for metric in metrics:
            data.append(Metric(**metric))
        return data

    def __repr__(self):
        tags = list(self._tags.keys())
        if tags:
            tags.sort()
            tags = ' ' + (' '.join(
                '{}={}'.format(k, self._tags[k])
                for k in tags
            ))

        return '<Warp10Client {}>'.format(tags or '')
