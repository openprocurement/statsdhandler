# coding=utf-8
import logging
import mock
import os
import random
import unittest

from statsd import (
    Connection,
    compat
)

from statsdhandler.statsdhandler import StatsdHandler


class StatsdHandlerTestCase(unittest.TestCase):
    """"""
    def connection_send(self, data, sample_rate=None):
        if self._disabled:
            self.logger.debug('Connection disabled, not sending data')
            return False
        if sample_rate is None:
            sample_rate = self._sample_rate

        sampled_data = {}
        if sample_rate < 1:
            if random.random() <= sample_rate:
                # Modify the data so statsd knows our sample_rate
                for stat, value in compat.iter_dict(data):
                    sampled_data[stat] = '%s|@%s' % (data[stat], sample_rate)
        else:
            sampled_data = data

        try:
            for stat, value in compat.iter_dict(sampled_data):
                send_data = ('%s:%s' % (stat, value)).encode("utf-8")

                # sending via UDP replaced by writing to file
                with open('{0}/test_output.txt'.format(os.getcwd()), 'a') as output_file:
                    output_file.write('{0}\n'.format(send_data))

            return True
        except Exception as e:
            self.logger.exception('unexpected error %r while sending data', e)
            return False

    def connection_send_fail(*args, **kwargs):
        raise Exception('some exception')

    def setUp(self):
        self.logger = logging.getLogger('statsd_handler')
        self.logger.setLevel(logging.DEBUG)

        sdh = StatsdHandler(args='statsdhandler/tests/config.yaml')
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

    @mock.patch.object(Connection, 'send', connection_send)
    def test_counter_metrics(self):

        # invalid type of value

        self.logger.info('Increment counter', extra={'REQUEST_DUR_CUSTOM': {}})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        # invalid key

        self.logger.info('Increment counter', extra={'JOURNAL_REQUEST_METHOD_2': 'INVALID_KEY'})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        self.logger.info('Increment counter', extra={'JOURNAL_REQUEST_METHOD_2': 'PUT'})
        with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
            self.assertEqual(output_file.read(), 'default_app_key.statsd_handler;JOURNAL_REQUEST_METHOD_2;PUT:1|c\n')

        self.logger.info('Decrement counter', extra={'REQUEST_DUR': -3})
        with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
            self.assertEqual(output_file.read(),
                             'default_app_key.statsd_handler;JOURNAL_REQUEST_METHOD_2;PUT:1|c\n' +
                             'default_app_key.statsd_handler;REQUEST_DUR;REQUEST_DUR:3|c\n' +
                             'default_app_key.REQUEST_DUR;REQUEST_DUR:3|c\n' +
                             'default_app_key.REQUEST_DUR:3|c\n'
                             )

        # Unexpected exception

        with mock.patch.object(Connection, 'send', StatsdHandlerTestCase.connection_send_fail):
            self.logger.info('Increment counter', extra={'JOURNAL_REQUEST_METHOD_2': 'PUT'})

    @mock.patch.object(Connection, 'send', connection_send)
    def test_gauge_metrics(self):

        # without value

        self.logger.info('Gauge increment', extra={'JOURNAL_GAUGE_ATTR': None})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        self.logger.info('Gauge increment', extra={'JOURNAL_GAUGE_ATTR': 42})
        with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
            self.assertEqual(output_file.read(), 'default_app_key.statsd_handler;JOURNAL_GAUGE_ATTR;gauge_name:+42|g\n')

        self.logger.info('Gauge decrement', extra={'JOURNAL_GAUGE_ATTR_DECR': 9000})
        with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
            self.assertEqual(output_file.read(),
                             'default_app_key.statsd_handler;JOURNAL_GAUGE_ATTR;gauge_name:+42|g\n' +
                             'default_app_key.statsd_handler;JOURNAL_GAUGE_ATTR_DECR;gauge_decrement_name:-9000|g\n'
                             )

        self.logger.info('Gauge send', extra={'JOURNAL_GAUGE_ATTR_DEFAULT': 15})
        with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
            self.assertEqual(output_file.read(),
                             'default_app_key.statsd_handler;JOURNAL_GAUGE_ATTR;gauge_name:+42|g\n' +
                             'default_app_key.statsd_handler;JOURNAL_GAUGE_ATTR_DECR;gauge_decrement_name:-9000|g\n'
                             'default_app_key.statsd_handler;JOURNAL_GAUGE_ATTR_DEFAULT;gauge_default_action:15|g\n'
                             )

        # Unexpected exception

        with mock.patch.object(Connection, 'send', StatsdHandlerTestCase.connection_send_fail):
            self.logger.info('Gauge increment', extra={'JOURNAL_GAUGE_ATTR': 42})

    @mock.patch.object(Connection, 'send', connection_send)
    def test_timer_metrics(self):

        # without start_attr_name

        self.logger.info('Timer start-end', extra={'JOURNAL_REQUEST_START_1': None, 'JOURNAL_REQUEST_END_1': 42})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        # without value_attr_name

        self.logger.info('Timer duration', extra={'JOURNAL_REQUEST_DUR_TIME': None})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        # invalid start_attr_name

        self.logger.info('Timer start-end', extra={'JOURNAL_REQUEST_START_1': 'one', 'JOURNAL_REQUEST_END_1': 42})
        with self.assertRaises(IOError) as e:
            open('{0}/test_output.txt'.format(os.getcwd()), 'r')
        self.assertEqual(e.exception.strerror, 'No such file or directory')

        self.logger.info('Timer start-end', extra={'JOURNAL_REQUEST_START_1': 0, 'JOURNAL_REQUEST_END_1': 42})
        with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
            self.assertEqual(output_file.read(),
                             'default_app_key.statsd_handler;;timer_name:42000.00000000|ms\n')

        self.logger.info('Timer duration', extra={'JOURNAL_REQUEST_DUR_TIME': 15})
        with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
            self.assertEqual(output_file.read(),
                             'default_app_key.statsd_handler;;timer_name:42000.00000000|ms\n' +
                             'default_app_key.statsd_handler;;timer_name_3:15000.00000000|ms\n')

        # default publish template

        self.logger.info('Timer duration', extra={'JOURNAL_REQUEST_DUR_TIME_3': 20})
        with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
            self.assertEqual(output_file.read(),
                             'default_app_key.statsd_handler;;timer_name:42000.00000000|ms\n' +
                             'default_app_key.statsd_handler;;timer_name_3:15000.00000000|ms\n' +
                             'default_app_key.statsd_handler;;timer_name_5:20000.00000000|ms\n')

        # default publish template

        self.logger.info('Timer start-end', extra={'JOURNAL_REQUEST_START_2': 20, 'JOURNAL_REQUEST_END_3': 60})
        with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
            self.assertEqual(output_file.read(),
                             'default_app_key.statsd_handler;;timer_name:42000.00000000|ms\n' +
                             'default_app_key.statsd_handler;;timer_name_3:15000.00000000|ms\n' +
                             'default_app_key.statsd_handler;;timer_name_5:20000.00000000|ms\n' +
                             'default_app_key.statsd_handler;;timer_name_6:40000.00000000|ms\n')

        # Unexpected exception

        with mock.patch.object(Connection, 'send', StatsdHandlerTestCase.connection_send_fail):
            self.logger.info('Timer start-end', extra={'JOURNAL_REQUEST_START_1': 0, 'JOURNAL_REQUEST_END_1': 42})


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StatsdHandlerTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
