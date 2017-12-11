#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from mock import mock
import requests

import warp10client
from warp10client.tests import base
from warp10client.timeserie import Timeserie


class TestWarp10ClientTestCase(base.BaseTestCase):

    def setUp(self):
        super(TestWarp10ClientTestCase, self).setUp()
        self.mock_session = mock.Mock()
        self.mock_response = mock.Mock()
        self.write_token = str(uuid.uuid4())
        self.read_token = str(uuid.uuid4())
        self.resource_id = str(uuid.uuid4())
        self.project_id = str(uuid.uuid4())
        self.warp10_url = 'http://example.warp10.com'
        self.metric_name = 'cpu_util'
        self.app = 'example.project_name'
        self.expected_value = 0.721909255255
        self.expected_timestamp = 1506398400000000
        self.expected_unit = '%'
        self.metric_write = {
            'name': self.metric_name,
            'tags': {
                'resource_id': self.resource_id,
                'project_id': self.project_id,
                'unit': self.expected_unit,
            },
            'position': {
                'longitude': None,
                'latitude': None,
                'elevation': None,
                'timestamp': self.expected_timestamp,
            },
            'value': self.expected_value,
        }
        self.metric_get = {
            'name': self.metric_name,
            'tags': {
                'resource_id': self.resource_id,
                'project_id': self.project_id,
            },
            'aggregate': {
                'type': 'mean',
                'span': 1000000 * 3600,
            },
            'timestamp': {
                'start': "2017-01-01T00:00:00.000Z",
                'end': "2018-01-01T00:00:00.000Z"
            }
        }

    def test_call_fetch(self):
        self.mock_response.status_code = 200
        self.mock_session.post = mock.Mock(return_value=self.mock_response)
        expected_url = self.warp10_url + '/exec'
        expected_headers = {
            'X-Warp10-Token': self.read_token,
        }

        with mock.patch('requests.Session', return_value=self.mock_session):
            client = warp10client.Warp10Client(write_token=self.write_token,
                                               read_token=self.read_token,
                                               warp10_api_url=self.warp10_url)
            client._call(self.metric_get, call_type='fetch')
            self.mock_session.post.assert_called_with(expected_url,
                                                      data=mock.ANY,
                                                      headers=expected_headers)

    def test_call_ingress(self):
        self.mock_response.status_code = 200
        self.mock_session.post = mock.Mock(return_value=self.mock_response)
        expected_url = self.warp10_url + '/update'
        expected_headers = {
            'X-Warp10-Token': self.write_token,
            'Content-Type': 'text/plain'
        }

        with mock.patch('requests.Session', return_value=self.mock_session):
            client = warp10client.Warp10Client(write_token=self.write_token,
                                               read_token=self.read_token,
                                               warp10_api_url=self.warp10_url)
            client._call(self.metric_write, call_type='ingress')
            self.mock_session.post.assert_called_with(expected_url,
                                                      data=mock.ANY,
                                                      headers=expected_headers)

    def test_get_resp_200(self):
        self.mock_response.status_code = 200
        self.mock_session.post = mock.Mock(return_value=self.mock_response)
        string_args = [self.metric_name, self.resource_id,
                       self.project_id, self.app, "{}",
                       self.expected_timestamp, self.expected_value]

        resp_content = '[[{{"c":"{}","l":{{"resource_id":"{}",'\
                       '"project_id":"{}",".app":"{}"}},"a":{}'\
                       ',"v":[[{},{}]]}}]]'.format(*string_args)

        self.mock_response.content = resp_content
        expected_tags = {
            'resource_id': str(self.resource_id),
            'project_id': str(self.project_id),
            '.app': self.app
        }

        with mock.patch('requests.Session', return_value=self.mock_session):
            client = warp10client.Warp10Client(write_token=self.write_token,
                                               read_token=self.read_token,
                                               warp10_api_url=self.warp10_url)
            timeserie = client.get(self.metric_get)
            self.assertIsInstance(timeserie, Timeserie)
            self.assertEqual(timeserie.metrics[0].name, self.metric_name)
            self.assertEqual(timeserie.metrics[0].value, self.expected_value)
            self.assertEqual(timeserie.metrics[0]._tags, expected_tags)
            self.assertEqual(timeserie.metrics[0].position.timestamp,
                             self.expected_timestamp)

    def test_get_resp_503(self):
        self.mock_response.status_code = 503
        self.mock_session.post = mock.Mock(return_value=self.mock_response)

        with mock.patch('requests.Session', return_value=self.mock_session):
            client = warp10client.Warp10Client(write_token=self.write_token,
                                               read_token=self.read_token,
                                               warp10_api_url=self.warp10_url)
            self.assertRaises(requests.RequestException,
                              client.get, self.metric_get)

    def test_exists_metric_exists(self):
        mock_response = mock.Mock()
        mock_response.status_code.return_value = 200
        string_args = [self.metric_name, self.resource_id,
                       self.project_id, self.app, "{}",
                       self.expected_timestamp, self.expected_value]

        resp_content = '[[{{"c":"{}","l":{{"resource_id":"{}",'\
                       '"project_id":"{}",".app":"{}"}},"a":{}'\
                       ',"v":[[{},{}]]}}]]'.format(*string_args)

        mock_response.content = resp_content

        with mock.patch(
                'requests.Session', return_value=self.mock_session
        ), mock.patch(
                'warp10client.client.Warp10Client._call',
                return_value=mock_response
        ):
            client = warp10client.Warp10Client(write_token=self.write_token,
                                               read_token=self.read_token,
                                               warp10_api_url=self.warp10_url)
            self.assertTrue(client.exists(self.metric_get))

    def test_exists_non_exist(self):
        mock_response = mock.Mock()
        mock_response.status_code.return_value = 200

        resp_content = '[[]]'
        mock_response.content = resp_content

        with mock.patch(
                'requests.Session', return_value=self.mock_session
        ), mock.patch(
                'warp10client.client.Warp10Client._call',
                return_value=mock_response
        ):
            client = warp10client.Warp10Client(write_token=self.write_token,
                                               read_token=self.read_token,
                                               warp10_api_url=self.warp10_url)
            self.assertFalse(client.exists(self.metric_get))

    def test_delete(self):
        with mock.patch('requests.Session', return_value=self.mock_session):
            client = warp10client.Warp10Client(write_token=self.write_token,
                                               read_token=self.read_token,
                                               warp10_api_url=self.warp10_url)
            self.assertRaises(NotImplementedError,
                              client.delete, self.metric_write)

    def test__call__gen_requests_body(self):
        with mock.patch('warp10client.client.Warp10Client._gen_request_body',
                        side_effect=warp10client.client.CallException):

            client = warp10client.Warp10Client(write_token=self.write_token,
                                               read_token=self.read_token,
                                               warp10_api_url=self.warp10_url)

            self.assertRaises(warp10client.client.CallException,
                              client._call, self.metric_write)

    def test__call__get_method(self):
        with mock.patch('warp10client.client.Warp10Client._get_method',
                        side_effect=warp10client.client.CallException):

            client = warp10client.Warp10Client(write_token=self.write_token,
                                               read_token=self.read_token,
                                               warp10_api_url=self.warp10_url)
            self.assertRaises(warp10client.client.CallException,
                              client._call, self.metric_write)
