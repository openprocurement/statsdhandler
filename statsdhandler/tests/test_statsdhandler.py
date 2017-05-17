# coding=utf-8
import logging
import mock
import os
import random
import unittest

from statsdhandler.statsdhandler import StatsdHandler
from datadog.dogstatsd import DogStatsd


class MockDogStatsd(DogStatsd):

    def _send_to_server(self, packet):
        try:
            with open('{0}/test_output.txt'.format(os.getcwd()),
                      'w') as output_file:
                output_file.write('{0}\n'.format(packet.encode(self.encoding)))
        except:
            pass


class StatsdHandlerTestCase(unittest.TestCase):
    """"""
    def get_text_from_doc(self):
        text = None
        try:
            with open('{0}/test_output.txt'.format(os.getcwd()),
                      'r') as output_file:
                text = output_file.read()
        except IOError:
            text = None
        return text

    def setUp(self):
        self.logger = logging.getLogger('statsd_handler')
        self.logger.setLevel(logging.DEBUG)

        sdh = StatsdHandler(args='statsdhandler/tests/config.yaml')
        sdh.statsd = MockDogStatsd(namespace='default_app_key')
        sdh.setLevel(logging.DEBUG)
        self.logger.addHandler(sdh)

    def tearDown(self):
        try:
            os.remove('{0}/test_output.txt'.format(os.getcwd()))
        except OSError:
            pass
        finally:
            self.logger.handlers = []

    def test_invalid_config_path(self):

        with self.assertRaises(Exception) as e:
            StatsdHandler(config_path='statsdhandler/tests/test_invalid.yml')
        self.assertEqual(e.exception.message, 'Invalid path to config file.')

    def test_counter_metrics(self):

        # invalid type of value
        self.logger.info('Increment counter', extra={'REQUEST_DUR_CUSTOM': {}})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        # invalid key
        self.logger.info('Increment counter',
                         extra={'JOURNAL_REQUEST_METHOD_2': 'INVALID_KEY'})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        self.logger.info('Increment counter',
                         extra={'JOURNAL_REQUEST_METHOD_2': 'PUT'})
        with open('{0}/test_output.txt'.format(os.getcwd()),
                  'r') as output_file:
            self.assertEqual(
                output_file.read(),
                'default_app_key.statsd_handler;JOURNAL_REQUEST_METHOD_2;'
                'PUT:1|c\n')

        self.logger.info('Decrement counter', extra={'REQUEST_DUR': -3})
        with open('{0}/test_output.txt'.format(os.getcwd()),
                  'r') as output_file:
            self.assertEqual(output_file.read(),
                             'default_app_key.REQUEST_DUR:3|c\n')

    def test_gauge_metrics(self):

        # without value
        self.logger.info('Gauge increment', extra={'JOURNAL_GAUGE_ATTR': None})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        self.logger.info('Gauge increment', extra={'JOURNAL_GAUGE_ATTR': 42})
        with open('{0}/test_output.txt'.format(os.getcwd()),
                  'r') as output_file:
            self.assertEqual(
                output_file.read(),
                'default_app_key.statsd_handler;JOURNAL_GAUGE_ATTR;'
                'JOURNAL_GAUGE_ATTR:42|g\n')

        self.logger.info('Gauge decrement',
                         extra={'JOURNAL_GAUGE_ATTR_DECR': 9000})
        with open('{0}/test_output.txt'.format(os.getcwd()),
                  'r') as output_file:
            self.assertEqual(
                output_file.read(),
                'default_app_key.statsd_handler;JOURNAL_GAUGE_ATTR_DECR;'
                'JOURNAL_GAUGE_ATTR_DECR:9000|g\n')

        self.logger.info('Gauge send',
                         extra={'JOURNAL_GAUGE_ATTR_DEFAULT': 15})
        with open('{0}/test_output.txt'.format(os.getcwd()),
                  'r') as output_file:
            self.assertEqual(
                output_file.read(),
                'default_app_key.statsd_handler;JOURNAL_GAUGE_ATTR_DEFAULT;'
                'JOURNAL_GAUGE_ATTR_DEFAULT:15|g\n')

    def test_timer_metrics(self):

        # without start_attr_name
        self.logger.info('Timer start-end',
                         extra={'JOURNAL_REQUEST_START_1': None,
                                'JOURNAL_REQUEST_END_1': 42})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        # without value_attr_name
        self.logger.info('Timer duration',
                         extra={'JOURNAL_REQUEST_DUR_TIME': None})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        # invalid start_attr_name
        self.logger.info('Timer start-end',
                         extra={'JOURNAL_REQUEST_START_1': 'one',
                                'JOURNAL_REQUEST_END_1': 42})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        self.logger.info('Timer start-end',
                         extra={'JOURNAL_REQUEST_START_1': 0,
                                'JOURNAL_REQUEST_END_1': 42})
        with open('{0}/test_output.txt'.format(os.getcwd()),
                  'r') as output_file:
            self.assertEqual(
                output_file.read(),
                'default_app_key.statsd_handler;;timer_name:42.0|ms\n')

        self.logger.info('Timer duration',
                         extra={'JOURNAL_REQUEST_DUR_TIME': 15})
        with open('{0}/test_output.txt'.format(os.getcwd()),
                  'r') as output_file:
            self.assertEqual(
                output_file.read(),
                'default_app_key.statsd_handler;;timer_name_3:15|ms\n')

        # default publish template
        self.logger.info('Timer duration',
                         extra={'JOURNAL_REQUEST_DUR_TIME_3': 20})
        with open('{0}/test_output.txt'.format(os.getcwd()),
                  'r') as output_file:
            self.assertEqual(
                output_file.read(),
                'default_app_key.statsd_handler;;timer_name_5:20|ms\n')

        # default publish template
        self.logger.info('Timer start-end',
                         extra={'JOURNAL_REQUEST_START_2': 20,
                                'JOURNAL_REQUEST_END_3': 60})
        with open('{0}/test_output.txt'.format(os.getcwd()),
                  'r') as output_file:
            self.assertEqual(
                output_file.read(),
                'default_app_key.statsd_handler;;timer_name_6:40.0|ms\n')

    def test_histogram_metrics(self):
        self.logger.info('Send histogram value', extra={'HISTOGRAM_ARG': None})
        self.assertEqual(self.get_text_from_doc(), None)
        self.logger.info('Send histogram value', extra={'HISTOGRAM_ARG_2': 5})
        self.assertEqual(
            self.get_text_from_doc(),
            'default_app_key.statsd_handler;HISTOGRAM_ARG_2;'
            'HISTOGRAM_ARG_2:5|h\n')
        self.logger.info('Send histogram value', extra={'HISTOGRAM_ARG_3': 4})
        self.assertEqual(
            self.get_text_from_doc(),
            'default_app_key.statsd_handler;HISTOGRAM_ARG_3;'
            'HISTOGRAM_ARG_3:4|h\n')

    def test_set_metrics(self):
        self.logger.info('Send set value', extra={'SET_ARG': None})
        self.assertEqual(self.get_text_from_doc(), None)
        self.logger.info('Send set value', extra={'SET_ARG_2': 1})
        self.assertEqual(
            self.get_text_from_doc(),
            'default_app_key.statsd_handler;SET_ARG_2;SET_ARG_2:1|s\n')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StatsdHandlerTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
