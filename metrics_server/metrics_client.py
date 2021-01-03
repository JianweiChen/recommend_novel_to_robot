# coding=utf8
import os
import json
import requests
import collections

class CounterInfo(object):
    def __init__(self):
        self.min_period = 0
        self.max_period = 0
        self.period_value_map = collections.defaultdict(int)
    def add(self, period, value):
        self.min_period = min(max(1, self.min_period), period)
        self.max_period = max(self.max_period, period)
        self.period_value_map[period] += value
    def __repr__(self):
        repr_message = 'min={}, max={}, dot_count={} ,value_avg={}'.format(
            self.min_period, self.max_period,
            len(self.period_value_map),
            sum(self.period_value_map.values()) / len(self.period_value_map)
        )
        return repr_message

class StoreInfo(object):
    def __init__(self):
        self.min_period = 0
        self.max_period = 0
        self.period_value_map = collections.defaultdict(int)
    def add(self, period, value):
        self.min_period = min(max(1, self.min_period), period)
        self.max_period = max(self.max_period, period)
        self.period_value_map[period] = value
    def __repr__(self):
        repr_message = 'min={}, max={}, dot_count={}'.format(
            self.min_period, self.max_period,
            len(self.period_value_map)
        )
        return repr_message

class TimerInfo(object):
    def __init__(self):
        self.min_period = 0
        self.max_period = 0
        self.period_value_set_map = collections.defaultdict(set)
    def add(self, period, value):
        self.min_period = min(max(1, self.min_period), period)
        self.max_period = max(self.max_period, period)
        self.period_value_set_map[period].add(value)
    def __repr__(self):
        repr_message = 'min={}, max={}, dot_count={}'.format(
            self.min_period, self.max_period,
            len(self.period_value_set_map)
        )
        return repr_message

class MetricsClient(object):
    def __init__(self, action_machine, name="default"):
        self.name = name
        self.action_machine = action_machine
        self.base_url = 'http://localhost:8001/'
        self._counter_map = collections.defaultdict(CounterInfo)
        self._timer_map = collections.defaultdict(TimerInfo)
        self._store_map = collections.defaultdict(StoreInfo)
    
    def emit_counter(self, query, value):
        period = self.action_machine._period
        self._counter_map[query].add(period, value)

    def emit_store(self, query, value):
        period = self.action_machine._period
        self._store_map[query].add(period, value)

    def emit_timer(self, query, value):
        period = self.action_machine._period
        self._timer_map[query].add(period, value)
    
    def get_period_data(self, period):
        data = {}
        # counter: rate, acc
        for query, counter_info in self._counter_map.items():
            counter_value = counter_info.period_value_map[period]
            key = '{}:rate'.format(query)
            data[key] = counter_value
        # timer: max, min, avg, count
        for query, timer_info in self._timer_map.items():
            key_max = '{}:max'.format(query)
            key_min = '{}:min'.format(query)
            key_avg = '{}:avg'.format(query)
            key_count = '{}:count'.format(query)
            timer_value_set = timer_info.period_value_set_map[period]
            data[key_max] = max(timer_value_set)
            data[key_min] = min(timer_value_set)
            data[key_avg] = sum(timer_value_set) / len(timer_value_set)
            data[key_count] = len(timer_value_set)
        # store
        for query, store_info in self._store_map.items():
            key = query
            data[key] = store_info.period_value_map[period]
        return data
    
    def post_to_metrics_server(self, period):
        # offline2recommend:rate, click_drive_delay:avg
        url = self.base_url + 'emit_period'
        period_data_message = json.dumps(self.get_period_data(period))
        requests.post(url, data={'name': self.name, 'period_data': period_data_message, 'period': period})
    
    def clear_all(self):
        self._counter_map.clear()
        self._timer_map.clear()
        self._store_map.clear()
        url = self.base_url + 'clear?name=' + self.name
        requests.post(url)

class FakeActionMachine(object):
    def __init__(self):
        self._period = 1
    def next_period(self):
        self._period += 1

if __name__ == '__main__':
    am = FakeActionMachine()
    metrics_client = MetricsClient(am, name='default')
    metrics_client.emit_counter('offline2recommend',2)
    metrics_client.emit_counter('offline2recommend',4)
    metrics_client.emit_timer('click_drive', 1.1)
    metrics_client.emit_timer('click_drive', 1.5)
    metrics_client.emit_timer('click_drive', 0.99)

    metrics_client.post_to_metrics_server(am._period)

    # r=metrics_client.get_period_data(1)
    # print(r)
        