import os
import sys
import random
import collections
import logging
import numpy as np
from novel_helper import NovelHelper, S
from args import Args

from event_manager import EventManager


# 机器人用户当前的状态
class RobotStatus:
    OFFLINE = 0
    RECOMMEND = 1
    CHOOSING = 2
    CLICK_DRIVE = 3;
    READ_DRIVE = 4;
    READING = 5;

# 1万个用户，流失80%，还剩2000人
class RobotUser:
    # DIO
    def __init__(self, robot_def):
        self.robot_def = robot_def
        self.uid = robot_def.uid

        self.choosing_bid_list = [] # 由recommend_sys填充
        self.choosing_delay = 0
        self.reading_bid = None
        self.chosen_bid_set = set() # 用于这一刷推荐中会点击的书
        
        self.reading_chapter = 0
        self.chapter_finish_delay = 0

        # 以下四个字段控制用户是否打开app或继续使用app
        self.addict_value = Args.addict_value_init_value
        self.addict_value_restore_rate = Args.addict_value_restore_rate_init_value
        self.detest_value = Args.detest_value_init_value
        self.detest_value_restore_rate = Args.detest_value_restore_rate_init_value

        self.status = RobotStatus.OFFLINE
        

        self.history_impr_map = dict() # 对已经推过的文章且没阅读过的，各种驱动值都会适当降低
        self.history_read_map = dict() # 已经阅读过的


        self._uid = robot_def.uid
        self._robot_def = robot_def
        self._status = RobotStatus.OFFLINE

        self._choosing_bid_list = []
        self._choosing_delay = 0
        self._reading_bid = None
        self._chosen_bid_set = set()
        self._reading_chapter = 0
        self._chapter_finish_delay = 0

        self._use_app_impulse_value = 0.
        self._addict_rate = 0. # 范围是-1.0到+1.0
        self._detest_rate = 0. # 范围是-1.0到+1.0
    
        self._history_impr_map = dict()
        self._history_read_map = dict()

        # 用于计算addict_value
        self._recent_click_drive_score_list = []
        self._recent_read_drive_score_list = []
        self._recent_detest_drive_score_list = []
        self._recent_title_detest_drive_score_list = []
        self._recent_addict_drive_score_list = []