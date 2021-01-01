# coding=utf8
import os, sys, random, collections, time
from novel_helper import NovelHelper, S
from args import Args

import numpy as np
import pandas as pd

from proto.user_def_pb2 import Robot as RobotDef, RobotRegiment, RobotArmy, EnlightenInfo

class EnlightenHelper:
    uid_string_bits = 12
 
    def __init__(self, robot_army=None, novel_helper=None):
        if not robot_army:
            self.robot_army = RobotArmy()
        else:
            self.robot_army = robot_army
        if not novel_helper:
            self.nh = NovelHelper()
        else:
            self.nh = novel_helper
        self.uid_set = set()
        self.load_uid_set()
        self.word_book_count_map = self.nh.word_book_count_map
        self.word_list = self.nh.word_list
   
    @staticmethod
    def load_robot_army():
        army = RobotArmy()
        with open(Args.robot_army_path, 'rb') as f:
            army.ParseFromString(f.read())
            return army
    
    def allocate_uid(self, robot, force=False):
        if robot.uid and not force:
            return robot.uid
        robot_hash_text = ','.join(
            '%s_%.3f' % (ei.word, ei.weight)
            for ei in robot.ei
        )
        d = hash(robot_hash_text)
        uid = str(d)[-16:]
        while uid in self.uid_set:
            d = hash(uid)
            uid = str(d)[-16:]
        self.uid_set.add(uid)
        robot.uid = uid
        return uid

    def load_uid_set(self):
        pass

    # enlighten方式：随机30个词，按照出现范围从高到低排序
    # ，前15个用来驱动机器人的点击和章节阅读行为，中间10个用来驱动上瘾留存行为
    # ，剩下的驱动厌恶行为

    def robot_enlighten(self):
        robot = RobotDef()
        step = 0
        ei_list = []
        while len(ei_list) < 30 and step < 10000:
            step += 1
            word = random.choice(self.word_list)
            book_count = self.word_book_count_map[word]
            if book_count < 10:
                continue
            if not S.is_a_word(word):
                continue
            if word.lower() in S.stopword_set:
                continue
            ei = EnlightenInfo(
                word=word.lower(),
                book_count=book_count,
                weight = 0.99
            )
            ei_list.append(ei)
        ei_list = sorted(ei_list, key=lambda ei:ei.book_count, reverse=True)
        click_or_read_ei_list = ei_list[:15]
        addict_ei_list = ei_list[15:25]
        detest_ei_list = ei_list[25:]
        robot.ei.extend(click_or_read_ei_list)
        robot.addict_ei.extend(addict_ei_list)
        robot.detest_ei.extend(detest_ei_list)
        self.allocate_uid(robot)
        return robot
    
    def robot_regiment_enlighten(self):
        regiment = RobotRegiment()
        for _ in range(Args.robot_count_per_regiment):
            robot = self.robot_enlighten()
            regiment.robot.append(robot)
        return regiment
    
    def robot_army_enlighten(self):
        army = RobotArmy()
        regiment_count_per_army = 10
        for _ in range(regiment_count_per_army):
            army.regiment.append(self.robot_regiment_enlighten())
        return army
    
    def enlighten_and_dump(self):
        army = self.robot_army_enlighten()
        with open(Args.robot_army_path, 'wb') as fw:
            fw.write(army.SerializeToString())
        
    def get_robot_repr(self, robot):
        repr_list = []
        repr_list.append("[click_or_read]")
        for ei in robot.ei:
            word = ei.word
            cn = self.nh.get_cn(word)
            book_count = ei.book_count
            repr_list.append("%s_%s_%s" % (word, cn, book_count))
        repr_list.append("[addict]")
        for ei in robot.addict_ei:
            word = ei.word
            cn = self.nh.get_cn(word)
            book_count = ei.book_count
            repr_list.append("%s_%s_%s" % (word, cn, book_count))
        repr_list.append("[detest]")
        for ei in robot.detest_ei:
            word = ei.word
            cn = self.nh.get_cn(word)
            book_count = ei.book_count
            repr_list.append("%s_%s_%s" % (word, cn, book_count))  
        return ",".join(repr_list)
    
    def report_robot_army(self, robot_army):
        robot_regiment_count = len(robot_army.regiment)
        robot_count = 0
        for robot_regiment in robot_army.regiment:
            for robot in robot_regiment.robot:
                robot_count += 1
        report_message_list = []
        report_message_list.append('regiment_count: %s' % robot_regiment_count)
        report_message_list.append('robot_count: %s' % robot_count)
        report_message = ','.join(report_message_list)
        print(report_message)
        