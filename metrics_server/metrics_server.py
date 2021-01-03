# coding=utf8
from flask import Flask
from flask import render_template
from flask import send_from_directory
from flask import request
app = Flask(__name__)
import os
import sys
import collections
import json

class QueryValue(object):
    def __init__(self):
        self.min_period = 0
        self.max_period = 0
        self.period_value_map = collections.defaultdict(int)
    
    def add_point(self, period, value):
        self.min_period = min(max(self.min_period, 1), period)
        self.max_period = max(self.max_period, period)
        self.period_value_map[period] = value
    
    def get_json(self):
        data = dict()
        data['min_period'] = self.min_period
        data['max_period'] = self.max_period
        data['period_value_map'] = dict(self.period_value_map)
        return data

class MetricsGroup(object):
    def __init__(self):
        self._query_map = collections.defaultdict(QueryValue)
    
    def clear(self):
        self._query_map.clear()

metrics_group_map = collections.defaultdict(MetricsGroup)

@app.route('/emit_period', methods=['GET', 'POST'])
def emit_period():
    period_data_message = request.form.get('period_data')
    period = int(request.form.get('period', 0))
    metrics_group_name = request.form.get('name', 'default')
    if not period or not period_data_message:
        return 'fail'
    period_data = json.loads(period_data_message)
    metrics_group = metrics_group_map[metrics_group_name]
    for query, value in period_data.items():
        metrics_group._query_map[query].add_point(period, value)
    return 'ok'

@app.route('/debug', methods=['GET', 'POST'])
def debug():
    debug_json = {'name': 'debug'}
    for name, metrics_group in metrics_group_map.items():
        debug_json[name] = dict()
        for query, query_info in metrics_group._query_map.items():
            debug_json[name][query] = query_info.get_json()
    debug_message = json.dumps(debug_json)
    return debug_message

def _fill_rsp_data(name, use_query, rsp_data):
    metrics_group = metrics_group_map[name]
    for query in use_query.split(','):
        if query in metrics_group._query_map:
            x_data, y_data = [], []
            query_info = metrics_group._query_map[query]
            for period in range(query_info.min_period, query_info.max_period+1):
                x_data.append(period)
                y_data.append(query_info.period_value_map.get(period, 0))
            rsp_data[query] = {
                'x_data': x_data,
                'y_data': y_data,
                'type': 'store'
            }

@app.route('/query', methods=['GET', 'POST'])
def query():
    use_query = request.args.get('use_query')
    metrics_group_name = request.args.get('name', 'default')
    rsp_data = dict()
    for query_with_suffix in use_query.split(','):
        tps = query_with_suffix.split(':')
        query_type = 'store'
        if len(tps) > 1:
            suffix = tps[1]
            if suffix == 'rate':
                query_type = 'counter'
            elif suffix in ('avg', 'max', 'min', 'count'):
                query_type = 'timer'
        query = query_with_suffix
        _fill_rsp_data(metrics_group_name, query, rsp_data)
    return json.dumps(rsp_data)

@app.route('/monitor', methods=['GET', 'POST'])
def monitor():
    use_query = request.args.get('use_query')
    metrics_group_name = request.args.get('name', 'default')
    s = render_template('monitor.html', 
    use_counter_query=use_query,
    metrics_group_name=metrics_group_name
    )
    return s
@app.route('/clear', methods=['GET', 'POST'])
def clear():
    metrics_group_name = request.args.get('name', 'default')
    metrics_group = metrics_group_map[metrics_group_name]
    metrics_group.clear()
    return 'ok'

app.run('localhost', 8001, debug=True) 