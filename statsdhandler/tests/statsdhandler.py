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

import statsdhandler


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

    # def connection_send_fail(*args, **kwargs):
    #     raise Exception('some exception')

    def setUp(self):
        self.logger = logging.getLogger('statsd_handler')
        self.logger.setLevel(logging.DEBUG)

        sdh = StatsdHandler(
            config_path='statsdhandler/tests/conf.yaml')
        sdh.setLevel(logging.DEBUG)
        self.logger.addHandler(sdh)

    def tearDown(self):
        self.logger.handlers = []

    def test_invalid_config_path(self):

        with self.assertRaises(Exception) as e:
            StatsdHandler(config_path='statsdhandler/tests/test_invalid.yml')
        self.assertEqual(e.exception.message, 'Invalid path to config file.')

    # def test_invalid_metric_type(self):
    #     self.logger.info('Increment counter', extra={'MESSAGE_ID': 'DOCUMENT_UPDATE', 'perfdata.invalid.': 1})
    #     with self.assertRaises(IOError) as e:
    #         open('{0}/test_output.txt'.format(os.getcwd()), 'r')
    #     self.assertEqual(e.exception.strerror, 'No such file or directory')
    #
    # @mock.patch.object(Connection, 'send', connection_send)
    # def test_document_update(self):
    #     self.logger.info('Increment counter', extra={'MESSAGE_ID': 'DOCUMENT_UPDATE', 'perfdata.c.': 1})
    #     with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
    #         self.assertEqual(output_file.read(), 'app_key.statsd_handler;DOCUMENT_UPDATE;document_update:1|c\n')
    #
    #     # Unexpected exception
    #
    #     with mock.patch.object(Connection, 'send', StatsdHandlerTestCase.connection_send_fail):
    #         self.logger.info('Increment counter', extra={'MESSAGE_ID': 'DOCUMENT_UPDATE', 'perfdata.c.': 1})
    #
    # @mock.patch.object(Connection, 'send', connection_send)
    # def test_document_save(self):
    #     self.logger.info('Increment counter with some value', extra={'MESSAGE_ID': 'DOCUMENT_SAVE', 'perfdata.c.': 3})
    #     with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
    #         self.assertEqual(output_file.read(), 'app_key.statsd_handler;DOCUMENT_SAVE;document_save:3|c\n')
    #
    #     # Unexpected exception
    #
    #     with mock.patch.object(Connection, 'send', StatsdHandlerTestCase.connection_send_fail):
    #         self.logger.info('Increment counter with some value', extra={'MESSAGE_ID': 'DOCUMENT_SAVE', 'perfdata.c.': 3})
    #
    # @mock.patch.object(Connection, 'send', connection_send)
    # def test_indexation_progress(self):
    #     self.logger.info('Set dimension', extra={'MESSAGE_ID': 'INDEXATION_PROGRESS', 'perfdata.kv.index_name': 97})
    #     with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
    #         self.assertEqual(output_file.read(), 'app_key.statsd_handler;INDEXATION_PROGRESS;index_name:97|g\n')
    #
    #     # Unexpected exception
    #
    #     with mock.patch.object(Connection, 'send', StatsdHandlerTestCase.connection_send_fail):
    #         self.logger.info('Set dimension', extra={'MESSAGE_ID': 'INDEXATION_PROGRESS', 'perfdata.kv.index_name': 97})
    #
    # @mock.patch.object(Connection, 'send', connection_send)
    # def test_logging_duration(self):
    #     self.logger.debug('Timer metric', extra={'MESSAGE_ID': 'LOGGING_DURATION', 'perfdata.ms.metric_name': 42})
    #     with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
    #         self.assertEqual(output_file.read(),
    #                          'app_key.statsd_handler;LOGGING_DURATION;metric_name:42000.00000000|ms\n' +
    #                          'app_key.LOGGING_DURATION;metric_name:42000.00000000|ms\n' +
    #                          'app_key.metric_name:42000.00000000|ms\n'
    #                          )
    #
    #     # Unexpected exception
    #
    #     with mock.patch.object(Connection, 'send', StatsdHandlerTestCase.connection_send_fail):
    #         self.logger.debug('Timer metric', extra={'MESSAGE_ID': 'LOGGING_DURATION', 'perfdata.ms.metric_name': 42})
    #
    # @mock.patch.object(Connection, 'send', connection_send)
    # def test_power_level(self):
    #
    #     # Increment
    #
    #     self.logger.info('Increment power level', extra={'MESSAGE_ID': 'POWER_LEVEL', 'perfdata.g.': 9000})
    #     with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
    #         self.assertEqual(output_file.read(), 'app_key.statsd_handler;POWER_LEVEL;power_level:+9000|g\n')
    #
    #     try:
    #         os.remove('{0}/test_output.txt'.format(os.getcwd()))
    #     except OSError:
    #         pass
    #
    #     # Decrement
    #
    #     self.logger.info('Decrement power level', extra={'MESSAGE_ID': 'POWER_LEVEL', 'perfdata.g.': -9000})
    #     with open('{0}/test_output.txt'.format(os.getcwd()), 'r') as output_file:
    #         self.assertEqual(output_file.read(), 'app_key.statsd_handler;POWER_LEVEL;power_level:+9000|g\n')
    #
    #     # Not a number
    #
    #     self.logger.info('Decrement power level', extra={'MESSAGE_ID': 'POWER_LEVEL', 'perfdata.g.': 'nine_thousands'})
    #
    # @mock.patch.object(Connection, 'send', connection_send)
    # def test_invalid_record(self):
    #
    #     # Missing MESSAGE_ID
    #
    #     self.logger.info('Increment counter', extra={'perfdata.c.': 1})
    #     with self.assertRaises(IOError) as e:
    #         open('{0}/test_output.txt'.format(os.getcwd()), 'r')
    #     self.assertEqual(e.exception.strerror, 'No such file or directory')
    #
    #     # Too long perfdata identifier
    #
    #     self.logger.info('Increment counter', extra={'MESSAGE_ID': 'DOCUMENT_UPDATE', 'perfdata.c.too.long': 1})
    #     with self.assertRaises(IOError) as e:
    #         open('{0}/test_output.txt'.format(os.getcwd()), 'r')
    #     self.assertEqual(e.exception.strerror, 'No such file or directory')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StatsdHandlerTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
