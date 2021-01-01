# coding=utf8

import os
import sys
import random
import pandas as pd
import numpy as np
import sqlalchemy.types

from sqlalchemy import create_engine
from args import Args


"""功能包括
- 记录埋点并dump到硬盘
- 拼接训练样本（Joiner的功能在文档里讨论一下）
- 用sql统计
"""
class EventManager(object):
    field_list = [
        'event',
        'uid',
        'bid',
        'period',
        'duration'
    ]
    def __init__(self, action_machine):
        self.action_machine = action_machine # now, only use period field
        self.event_json_data_list = []
        self.engine = create_engine('sqlite://', echo=False)
        self.engine_prepared = False

    def clean_all_csv(self):
        filename_list = os.listdir(Args.event_csv_path)
        for filename in filename_list:
            if filename.endswith('.csv'):
                abs_path = os.path.join(Args.event_csv_path, filename)
                os.remove(abs_path)
    
    def _get_period_csv_file_path(self, period):
        return os.path.join(Args.event_csv_path, '%06d.csv' % period)

    def _flush_to_csv(self):
        period = self.action_machine._period
        period_event_csv_path = self._get_period_csv_file_path(period)
        if os.path.exists(period_event_csv_path):
            period_event_df = pd.read_csv(period_event_csv_path)
        else:
            period_event_df = pd.DataFrame(columns=self.field_list)
        period_event_df = period_event_df[self.field_list]
        period_event_df = pd.concat([period_event_df, pd.DataFrame(self.event_json_data_list)])
        period_event_df.to_csv(period_event_csv_path)
        self.event_json_data_list.clear()

    def emit_one_event(self, event, uid, bid, period=None, duration=None):
        self._try_to_flush_csv()
        json_data = dict()
        json_data['event'] = event
        json_data['uid'] = uid
        json_data['bid'] = bid
        if not period:
            period = self.action_machine.get_period()
        json_data['period'] = period
        if duration:
            json_data['duration'] = duration
        self.event_json_data_list.append(json_data)
        
    
    def _try_to_flush_csv(self):
        if len(self.event_json_data_list) < 1:
            return
        first_json_data = self.event_json_data_list[0]
        period = first_json_data['period']
        if period != self.action_machine._period:
            self._flush_to_csv()
    
    def prepare_sql_engine(self):
        period_df_list = []
        for filename in os.listdir(Args.event_csv_path):
            if not filename.endswith('.csv'): continue
            abs_path = os.path.join(Args.event_csv_path, filename)
            period_df = pd.read_csv(abs_path)
            period_df_list.append(period_df)
        sql_df = pd.concat(period_df_list)
        sql_df['bid'] = sql_df['bid'].astype('string')
        sql_df['uid'] = sql_df['uid'].astype('string')
        sql_df.to_sql(name='novel_event', con=self.engine, if_exists='replace',
            dtype={
                "bid": sqlalchemy.types.String, "uid": sqlalchemy.types.String, 
            })
        
    def query(self, sql_text, reprepare=True):
        if not self.engine_prepared or reprepare:
            self.prepare_sql_engine()
            self.engine_prepared = True
        r = self.engine.execute(sql_text).fetchall()
        return r
