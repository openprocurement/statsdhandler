# -*- coding: utf-8 -*-
import argparse
import os
from yaml import load
from datadog.dogstatsd import DogStatsd
import logging
import time


class StatsdHandler(logging.Handler):

    DEFAULT_PUBLISH_TEMPLATES = {
        'default': ['%(logger)s;%(attr)s;%(metric_name)s']
    }

    DEFAULT_CONFIG = {
        'app_key': 'default_app_key',
        'host': 'localhost',
        'port': 8125,
        'sample_rate': 1,
        'disabled': False
    }

    def __init__(self, args=None, config_path=None):
        logging.Handler.__init__(self)
        if args is not None and args != '':
            config_path = args
        if not os.path.isfile(config_path):
            raise Exception('Invalid path to config file.')
        with open(config_path) as config_file_obj:
            self.config = load(config_file_obj.read())
        for key in self.DEFAULT_CONFIG:
            setattr(self, key, self.config.get('main', {}).get(key, None) or
                    self.DEFAULT_CONFIG[key])

        # Initialize Statsd Client
        self.statsd = DogStatsd(
            host=self.host, port=self.port, namespace=self.app_key)

        self.publish_templates = self.DEFAULT_PUBLISH_TEMPLATES
        publish_templates = self.config.get('publish_templates', {})
        self.publish_templates.update(publish_templates)
        self.counters = self.config.get('counters', {})
        self.gauges = self.config.get('gauges', {})
        self.timers = self.config.get('timers', [])
        self.histograms = self.config.get('histograms', {})
        self.sets = self.config.get('sets', {})
        self.timers_start_keys = self._get_timers_keys_list('start')
        self.timers_end_keys = self._get_timers_keys_list('end')
        self.timers_value_keys = self._get_timers_keys_list('value')

    def _get_timers_keys_list(self, key_prefix):
        keys = []
        for t in self.timers:
            key = t.get('{}_attr_name'.format(key_prefix), None)
            if key is not None:
                keys.append(key)
        return keys

    def _get_timer_params(self, key_prefix, value_attr_name=None,
                          start_attr_name=None, end_attr_name=None):
        for t in self.timers:
            if key_prefix == 'start':
                if (t.get('start_attr_name', None) == start_attr_name and
                        t.get('end_attr_name', None) == end_attr_name):
                    return [t.get('name', start_attr_name),
                            t.get('publish_template', 'default')]
            elif key_prefix == 'value':
                if (t.get('value_attr_name', None) == value_attr_name):
                    return [t.get('name', value_attr_name),
                            t.get('publish_template', 'default')]
            else:
                return None, None

    def _publish_count(self, subname, value):
        try:
            if float(value) > 0:
                self.statsd.increment(subname, value)
            else:
                self.statsd.decrement(subname, value)
        except:
            pass

    def _publish_timer(self, subname, value):
        try:
            self.statsd.timing(subname, value)
        except:
            pass

    def _process_counter_metrics(self, attr, record):
        lookup_value = self.counters[attr].get('lookup_value', 'None')
        value = getattr(record, attr, None)
        value_type = self.counters[attr].get('value_type', 'key')
        value_equals = self.counters[attr].get('value_equals', [])
        publish_template = self.counters[attr].get('publish_template',
                                                   'default')
        if publish_template not in self.publish_templates:
            publish_template = 'default'
        if value_type == 'value':
            counter_subname = attr
            counter_value = value if value is not None else 1
        elif value_type == 'key':
            counter_subname = value if value is not None else lookup_value
            if len(value_equals) > 0 and value not in value_equals:
                return
            counter_value = 1
        else:
            return
        for pt in self.publish_templates[publish_template]:
            subname = pt % dict(
                logger=record.name,
                attr=attr,
                metric_name=counter_subname
            )
            self._publish_count(subname, counter_value)

    def _process_timer_metrics(self, attr, record, key_prefix):
        if key_prefix == 'start':
            start_attr_value = getattr(record, attr, None)
            if start_attr_value is None:
                return
            start_attr_name = attr
            end_attr_value = None
            for end_attr_name in self.timers_end_keys:
                end_attr_value = getattr(record, end_attr_name, None)
                if end_attr_value is not None:
                    try:
                        timer_value = float(end_attr_value) -\
                            float(start_attr_value)
                        timer_name, publish_template =\
                            self._get_timer_params(
                                key_prefix, start_attr_name=start_attr_name,
                                end_attr_name=end_attr_name)
                        if publish_template not in self.publish_templates:
                            publish_template = 'default'
                        if timer_name is not None:
                            for pt in self.publish_templates[publish_template]:
                                subname = pt % dict(
                                    logger=record.name,
                                    attr='',
                                    metric_name=timer_name)
                                self._publish_timer(subname, timer_value)
                    except:
                        pass
        elif key_prefix == 'value':
            timer_value = getattr(record, attr, None)
            if timer_value is None:
                return
            timer_name, publish_template = self._get_timer_params(
                key_prefix, value_attr_name=attr)
            if publish_template not in self.publish_templates:
                publish_template = 'default'
            if timer_name is not None:
                for pt in self.publish_templates[publish_template]:
                    subname = pt % dict(
                        logger=record.name,
                        attr='',
                        metric_name=timer_name)
                    self._publish_timer(subname, timer_value)

    def _get_publish_template(self, metric_type, attr):
        metric_types_dict = getattr(self, metric_type, {})
        if metric_type == 'sets':
            publisher = self.statsd.set
        elif metric_type == 'gauges':
            publisher = self.statsd.gauge
        elif metric_type == 'histograms':
            publisher = self.statsd.histogram
        else:
            publisher = None
        publish_template =\
            metric_types_dict[attr].get('publish_template', 'default')
        if publish_template not in self.publish_templates:
            publish_template = 'default'
        return publish_template, publisher

    def _process_metrics(self, metric_type, attr, record):
        value = getattr(record, attr, None)
        if value is not None:
            publish_template, publisher =\
                self._get_publish_template(metric_type, attr)
            for pt in self.publish_templates[publish_template]:
                subname = pt % dict(
                    logger=record.name,
                    attr=attr,
                    metric_name=attr)
                publisher(subname, value)

    def emit(self, record):
        for attr in dir(record):
            if attr in self.counters:
                self._process_counter_metrics(attr, record)
            elif attr in self.gauges:
                self._process_metrics('gauges', attr, record)
            elif attr in self.timers_start_keys:
                self._process_timer_metrics(attr, record, 'start')
            elif attr in self.timers_value_keys:
                self._process_timer_metrics(attr, record, 'value')
            elif attr in self.histograms:
                self._process_metrics('histograms', attr, record)
            elif attr in self.sets:
                self._process_metrics('sets', attr, record)
            else:
                continue
