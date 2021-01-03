import os
import sys
import random
import time
import collections
import logging
import numpy as np
from novel_helper import NovelHelper, S
from args import Args
from event_manager import EventManager
from robot import RobotUser, RobotStatus
from rec_sys.random_rec_sys import RecSysRandom
from metrics_server.metrics_client import MetricsClient

class Book:
    def __init__(self, book_def):
        self._book_def = book_def
        self._book_id = book_def.bid

# 关于消重，这个东西搞复杂了徒增内存消耗，意义不大
# 既然是机器人，也不必搞那么复杂，对行为驱动的影响会随着时间衰减
class ReadingInfo(object):
    def __init__(self, last_period, chapter, addict_value):
        self.last_period = last_period
        self.chapter = chapter
        # 对于某本书，只记addict_value，不记detect_value
        self.addict_value = addict_value
    def __repr__(self):
        return "chapter=%s, last_period=%s, addict_value=%s" % (self.chapter, 
            self.last_period, self.addict_value)

class ImpressionInfo(object):
    def __init__(self, last_period):
        self.last_period = last_period
    def __repr__(self):
        return "last_period=%s" % last_period


# am用于调度机器人行为
class ActionMachine(object):
    # DIO
    def __init__(self, novel_helper, robot_army):
        self.nh = novel_helper
        self.novel_helper = novel_helper
        self.book_warehouse = self.nh.book_warehouse
        self.robot_army = robot_army
        self.user_map = dict()
        self.init_user_map()
        self.book_map = dict()
        self.init_book_map()

        self.offline_uid_set = set(list(self.user_map.keys()))
        self.recommend_uid_set = set()
        self.choosing_uid_set = set()
        self.click_drive_uid_set = set()
        self.read_drive_uid_set = set()
        self.reading_uid_set = set()
        self.has_online_set = set()

        self._period = 0

        self.rec_sys = RecSysRandom(self)

        self.event_manager = EventManager(self)
        self.event_manager.clean_all_csv()

        self.metrics_client = MetricsClient(self)

    def get_period(self):
        return self._period

    def reset_timer(self):
        self.st = time.time()
    
    def timer_cost(self):
        return time.time() - self.st
    
    def emit_timer(self, query):
        time_cost = self.timer_cost()
        self.metrics_client.emit_timer(query, time_cost)

    # 统计查询，会先检查sqlite-in-memory的建表状态
    def query(self, sql_text, reprepare=True):
        r = self.event_manager.query(sql_text, reprepare)
        return r

    def connect_rec_sys(self, rec_sys):
        self.rec_sys = rec_sys

    def init_user_map(self):
        for regiment in self.robot_army.regiment:
            for robot in regiment.robot:
                uid = robot.uid
                robot_user = RobotUser(robot)
                self._init_use_app_info(robot_user)
                self.user_map[uid] = robot_user

    def init_book_map(self):
        for book_def in self.book_warehouse.book:
            bid = book_def.bid
            self.book_map[bid] = Book(book_def)

    def _fill_empty_word_list(self, word_list):
        word_list = [
            word for word in word_list if word in self.novel_helper.wv_word_idx_map
        ]
        if not word_list:
            word_list = ['empty', 'word', 'list']
        return word_list

    # 驱动分值：点击
    # click_drive_score, chapter_read_drive_score, open_app_drive_score, detest_drive_score
    def _get_robot_click_book_score(self, robot_user, book): 
        book_def = book.book_def
        title_word = list(book_def.title.word)
        synopsis_word = list(book_def.synopsis.word)
        book_word_list = self._fill_no_title(title_word + synopsis_word)
        user_word_list = [ei.word for ei in robot_user.robot_def.ei]
        book_vector = self._word_list_vector_pooling(book_word_list)
        user_vector = self._word_list_vector_pooling(user_word_list)
        score_sum = np.dot(book_vector, user_vector)
        score = score_sum / (len(book_word_list) * len(user_word_list))
        return score

    # 对word_list取词向量做pooling是常见操作
    def _word_list_vector_pooling(self, word_list):
        wv_word_idx_map = self.nh.wv_word_idx_map
        wv_vector = self.nh.wv_model.vectors
        word_idx_list = [
            wv_word_idx_map[word.lower()] for word in word_list 
        ]
        word_vector_list = [
            wv_vector[idx] for idx in word_idx_list
        ]
        sum_vector = np.sum(word_vector_list, axis=0)
        return sum_vector

    # book_word多会用到，robot_word会分成多个sub_robot_word_list与book_word_list做
    #  点积，这代表每次阅读机器人用户的关注点是不同的，同时也能引入随机量
    def _dot_robot_book(self, robot_word_list, book_word_list, sample_loop):
        robot_word_list = self._fill_empty_word_list(robot_word_list)
        book_word_list = self._fill_empty_word_list(book_word_list)
        kb = len(book_word_list)
        kr = len(robot_word_list)
        sample_word_count = (kr - 1) // sample_loop + 1
        sub_dot_score_list = []
        book_vector = self._word_list_vector_pooling(book_word_list)
        for _ in range(sample_loop):
            sub_robot_word_list = random.sample(robot_word_list, sample_word_count)
            krp = len(sub_robot_word_list)
            sub_robot_vector = self._word_list_vector_pooling(sub_robot_word_list)
            sub_dot_score = np.dot(sub_robot_vector, book_vector)
            sub_dot_score /= (kb * krp)
            sub_dot_score_list.append(sub_dot_score)
        dot_score = max(sub_dot_score_list)
        return dot_score

    # 机器人的点击驱动值计算
    def _get_click_drive_score(self, robot_user, book, sample_loop=Args.default_sample_loop):
        # 传入book而非book_def是因为这样后续能让book中pb_def外的字段来参与算分
        robot_def = robot_user._robot_def
        book_def = book._book_def
        robot_enlighten_info_list = robot_def.ei
        robot_enlighten_word_list = [
            enlighten_info.word for enlighten_info in robot_enlighten_info_list
        ]
        title_word_list = S.sentence_to_string_list(book_def.title)
        synopsis_word_list = S.sentence_to_string_list(book_def.synopsis)
        title_synopsis_word_list = title_word_list + synopsis_word_list
        click_drive_score = self._dot_robot_book(
            robot_enlighten_word_list, synopsis_word_list, sample_loop=sample_loop)
        return click_drive_score

    # 机器人阅读驱动值计算
    def _get_read_drive_score(self, robot_user, book, chapter, sample_loop=Args.default_sample_loop):
        robot_def = robot_user._robot_def
        book_def = book._book_def
        robot_enlighten_info_list = robot_def.ei
        robot_enlighten_word_list = [
            enlighten_info.word for enlighten_info in robot_enlighten_info_list
        ]
        paragraph_all_count = len(book_def.paragraph)
        assert paragraph_all_count >= chapter and chapter > 0, \
            "chapter must in range %s>=chapter>=1 but get %s" % (paragraph_all_count, chapter)
        to_read_paragraph = book_def.paragraph[chapter-1]
        paragraph_word_list = S.paragraph_to_string_list(to_read_paragraph)
        read_drive_score = self._dot_robot_book(
            robot_enlighten_word_list, paragraph_word_list, sample_loop=sample_loop)
        return read_drive_score

    # 机器人标题厌恶驱动值计算
    def _get_title_detest_drive_score(self, robot_user, book, sample_loop=Args.default_sample_loop):
        robot_def = robot_user._robot_def
        book_def = book._book_def
        robot_detest_info_list = robot_def.detest_ei
        robot_detest_word_list = [
            enlighten_info.word for enlighten_info in robot_detest_info_list
        ]
        title_word_list = S.sentence_to_string_list(book_def.title)
        synopsis_word_list = S.sentence_to_string_list(book_def.synopsis)
        title_synopsis_word_list = title_word_list + synopsis_word_list
        detest_drive_score = self._dot_robot_book(
            robot_detest_word_list, title_synopsis_word_list, sample_loop=sample_loop)
        return detest_drive_score

    # 机器人厌恶驱动值计算
    def _get_detest_drive_score(self, robot_user, book, chapter, sample_loop=Args.default_sample_loop):
        robot_def = robot_user._robot_def
        book_def = book._book_def
        robot_detest_info_list = robot_def.detest_ei
        robot_detest_word_list = [
            enlighten_info.word for enlighten_info in robot_detest_info_list
        ]
        paragraph_all_count = len(book_def.paragraph)
        assert paragraph_all_count >= chapter and chapter > 0, \
            "chapter must in range %s>=chapter>=1 but get %s" % (paragraph_all_count, chapter)
        to_read_paragraph = book_def.paragraph[chapter-1]
        paragraph_word_list = S.paragraph_to_string_list(to_read_paragraph)
        detest_drive_score = self._dot_robot_book(
            robot_detest_word_list, paragraph_word_list, sample_loop=sample_loop)
        return detest_drive_score

    # 机器人addict驱动值计算
    def _get_addict_drive_score(self, robot_user, book, chapter, sample_loop=Args.default_sample_loop):
        robot_def = robot_user._robot_def
        book_def = book._book_def
        robot_addict_info_list = robot_def.addict_ei
        robot_addict_word_list = [
            enlighten_info.word for enlighten_info in robot_addict_info_list
        ]
        paragraph_all_count = len(book_def.paragraph)
        assert paragraph_all_count >= chapter and chapter > 0, \
            "chapter must in range %s>=chapter>=1 but get %s" % (paragraph_all_count, chapter)
        to_read_paragraph = book.paragraph[chapter-1]
        paragraph_word_list = S.paragraph_to_string_list(to_read_paragraph)
        addict_drive_score = self._dot_robot_book(
            robot_addict_word_list, paragraph_word_list, sample_loop=sample_loop)
        return addict_drive_score

    # 计算机器人驱动值时加入的噪音
    def _get_normal_noise(self, noise_range=1.):
        return noise_range * random.gauss(0., 1.)

    # 维护recent_drive_score的队列并推入新值
    def _push_drive_score(self, recent_drive_score_list, drive_score):
        recent_drive_count = 5
        if len(recent_drive_score_list) >= recent_drive_count:
            recent_drive_score_list.pop(0)
        recent_drive_score_list.append(drive_score)

    # 在关闭app时做的收尾工作
    def _just_shut_down_app(self, robot_user):
        robot_user._use_app_impulse_value -= 0.5

    # 初始化机器人用户开关app的驱动信息
    def _init_use_app_info(self, robot_user):
        robot_user._use_app_impulse_value = random.random() - 0.99 # 有20%的用户会直接开app
        robot_user._addict_rate = random.random()
        robot_user._detest_rate = random.random()
    
    # 根据_recent_***那些变量俩计算
    def _update_addict_rate(self, robot_user):
        addict_rate_room_decay = .8
        addict_rate_room = 1. - robot_user._addict_rate
        addict_rate_room *= addict_rate_room_decay
        robot_user._addict_rate = 1. - addict_rate_room

    # 根据_recent_***那些变量俩计算
    def _update_detest_rate(self, robot_user):
        detest_rate_decay = .8
        robot_user._detest_rate *= detest_rate_decay
    
    # 打开app的冲动值
    def _update_offline_use_app_impulse_value(self, robot_user):
        for bid, reading_info in robot_user._history_read_map.items():
            bid_addict_value = reading_info.addict_value
            # 尚未想好bid_addict_value怎么影响_use_app_impulse_value
        delta = (robot_user._addict_rate - robot_user._detest_rate) * 1.
        robot_user._use_app_impulse_value += delta * Args.use_app_impluse_value_update_rate

    def _update_use_app_impulse_value(self, robot_user):
        pass

    # 第一状态——offline
    def _run_robot_offline(self, robot_user):
        if robot_user._use_app_impulse_value > 0:
            self.metrics_client.emit_counter('offline2recommend', 1)
            robot_user._status = RobotStatus.RECOMMEND
        else:
            robot_user._status = RobotStatus.OFFLINE
        self._update_offline_use_app_impulse_value(robot_user)
        self._update_addict_rate(robot_user)
        self._update_detest_rate(robot_user)
    
    # 第二状态——recommend
    def _run_robot_recommend(self, robot_user):
        self.rec_sys.recommend(robot_user)
        robot_user._chosen_bid_set.clear()
        robot_user._choosing_delay = 2
        robot_user._reading_bid = None
        robot_user._status = RobotStatus.CHOOSING
        for bid in robot_user._choosing_bid_list:
            self.event_manager.emit_one_event(uid=robot_user._uid, bid=bid, event='impression')
    
    # 第三状态——choosing
    def _run_robot_choosing(self, robot_user):
        if robot_user._choosing_delay > 0:
            robot_user._status = RobotStatus.CHOOSING
        else:
            robot_user._status = RobotStatus.CLICK_DRIVE
        robot_user._choosing_delay -= 1
    
    # 第四状态——click_drive
    def _run_robot_click_drive(self, robot_user):
        self.reset_timer()
        for bid in robot_user._choosing_bid_list:
            if bid in robot_user._chosen_bid_set:
                continue
            book = self.book_map[bid]
            click_drive_score = self._get_click_drive_score(
                robot_user, book, sample_loop=1)
            title_detest_drive_score = self._get_title_detest_drive_score(
                robot_user, book, sample_loop=1)
            if bid in robot_user._history_impr_map:
                suppress_rate = .5
            else:
                suppress_rate = 1.
            click_drive_score *= suppress_rate
            if title_detest_drive_score > Args.title_detest_drive_threshold:
                continue
            if click_drive_score > Args.click_drive_threshold:
                robot_user._reading_bid = bid
                robot_user._chosen_bid_set.add(bid)
                robot_user._history_read_map[bid] = ReadingInfo(
                    last_period=self._period,
                    chapter=0,
                    addict_value=0)
                self.event_manager.emit_one_event(uid=robot_user._uid, bid=bid, event='go_detail')
                break
            if random.random() < 0.1: # 10%的概率会被机器人记住“给我推过了”
                robot_user._history_impr_map[bid] = ImpressionInfo(last_period=self._period)
        if robot_user._reading_bid:
            robot_user._status = RobotStatus.READ_DRIVE
        else:
            # todo: not only OFFLINE, but also RECOMMEND
            robot_user._status = RobotStatus.OFFLINE
            self._just_shut_down_app(robot_user)
        self._update_use_app_impulse_value(robot_user)
        self.emit_timer('click_drive_delay')

    # 第五状态——read_drive
    def _run_robot_read_drive(self, robot_user):
        robot_user._status = RobotStatus.OFFLINE
        bid = robot_user._reading_bid
        book = self.book_map[bid]
        reading_info = robot_user._history_read_map[bid]
        # chapter记录的是之前读完哪一章了，之后从下一章开始读
        reading_info.chapter += 1
        if reading_info.chapter > len(book._book_def.paragraph):
            # 返回第一章继续阅读
            reading_info.chapter = 1
        read_drive_score = self._get_read_drive_score(
            robot_user,
            book,
            chapter=reading_info.chapter,
            sample_loop=1
        )
        detest_drive_score = self._get_detest_drive_score(
                robot_user, book, reading_info.chapter, sample_loop=1)
        if read_drive_score > Args.read_drive_threshold and detest_drive_score < Args.detest_drive_threshold:
            robot_user._status = RobotStatus.READING
            robot_user._chapter_finish_delay = 3
        else:
            robot_user._status = RobotStatus.CHOOSING
        self._update_use_app_impulse_value(robot_user)

    # 第六状态——reading
    def _run_robot_reading(self, robot_user):
        if robot_user._chapter_finish_delay > 0:
            robot_user._status = RobotStatus.READING
            robot_user._chapter_finish_delay -= 1
        else:
            robot_user._status = RobotStatus.READ_DRIVE

    # 一个period内的运行函数
    def run_one_period(self):
        self._period += 1
        for uid in self.offline_uid_set:
            robot_user = self.user_map[uid]
            self._run_robot_offline(robot_user)
        for uid in self.recommend_uid_set:
            robot_user = self.user_map[uid]
            self._run_robot_recommend(robot_user)
        for uid in self.choosing_uid_set:
            robot_user = self.user_map[uid]
            self._run_robot_choosing(robot_user)
        for uid in self.click_drive_uid_set:
            robot_user = self.user_map[uid]
            self._run_robot_click_drive(robot_user)
        for uid in self.read_drive_uid_set:
            robot_user = self.user_map[uid]
            self._run_robot_read_drive(robot_user)
        for uid in self.reading_uid_set:
            robot_user = self.user_map[uid]
            self._run_robot_reading(robot_user)
        self._update_robot_status()
        self._report_robot_user_status()
        self._metrics_emit_user_status()
        self._metrics_post_to_server()

    def run(self, k=Args.period_threshold):
        self.metrics_client.clear_all()
        self._period = 0
        try:
            while self._period+1 <= k:
                self.run_one_period()
        except KeyboardInterrupt:
            pass

    # 每个period最后会报告action_machine中各种用户的量
    def _report_robot_user_status(self):
        report_message_list = []
        report_message_list.append('period: %s' % self._period)
        report_message_list.append('offline: %s' % len(self.offline_uid_set))
        report_message_list.append('recommend: %s' % len(self.recommend_uid_set))
        report_message_list.append('choosing: %s' % len(self.choosing_uid_set))
        report_message_list.append('click_drive: %s' % len(self.click_drive_uid_set))
        report_message_list.append('read_drive: %s' % len(self.read_drive_uid_set))
        report_message_list.append('reading: %s' % len(self.reading_uid_set))
        # report_message_list.append('has_online: %s' % len(self.has_online_set))
        report_message = ','.join(report_message_list)
        sys.stdout.write('\r'+report_message+' '*10)
        # logging.error(report_message)
    
    def _metrics_emit_user_status(self):
        metrics_client = self.metrics_client
        metrics_client.emit_store('offline_uid', len(self.offline_uid_set))
        metrics_client.emit_store('recommend_uid', len(self.recommend_uid_set))
        metrics_client.emit_store('choosing_uid', len(self.choosing_uid_set))
        metrics_client.emit_store('click_drive_uid', len(self.click_drive_uid_set))
        metrics_client.emit_store('read_drive_uid', len(self.read_drive_uid_set))
        metrics_client.emit_store('reading_uid', len(self.reading_uid_set))
    
    def _metrics_post_to_server(self):
        self.metrics_client.post_to_metrics_server(self._period)

    # 在每一peroid结束时进行
    def _update_robot_status(self):
        self.offline_uid_set.clear()
        self.recommend_uid_set.clear()
        self.choosing_uid_set.clear()
        self.click_drive_uid_set.clear()
        self.read_drive_uid_set.clear()
        self.reading_uid_set.clear()

        for uid, robot_user in self.user_map.items():
            status = robot_user._status
            # sys.stdout.write('%s'%status)
            if status == RobotStatus.OFFLINE:
                self.offline_uid_set.add(uid)
            elif status == RobotStatus.RECOMMEND:
                self.recommend_uid_set.add(uid)
            elif status == RobotStatus.CHOOSING:
                self.choosing_uid_set.add(uid)
            elif status == RobotStatus.CLICK_DRIVE:
                self.click_drive_uid_set.add(uid)
            elif status == RobotStatus.READ_DRIVE:
                self.read_drive_uid_set.add(uid)
            elif status == RobotStatus.READING:
                self.reading_uid_set.add(uid)


def test_robot_click_book(am, k=1000):
    impr_cnt, click_cnt = 0, 0
    for _ in range(k):
        uid = random.choice(list(am.user_map.keys()))
        bid = random.choice(list(am.book_map.keys()))
        user, book = am.user_map[uid], am.book_map[bid]
        click = am.judge_robot_click_book(user, book)
        if click:
            click_cnt += 1
        impr_cnt += 1
    print('test_robot_click_book, impr=%s, click=%s, ctr=%s' % (impr_cnt, click_cnt, click_cnt / impr_cnt))

def test_robot_finish_chapter(am, k=1):
    for _ in range(k):
        uid = random.choice(list(am.user_map.keys()))
        bid = random.choice(list(am.book_map.keys()))
        user, book = am.user_map[uid], am.book_map[bid]
        for idx, paragraph in enumerate(book.book_def.paragraph):
            score = am._get_robot_finish_chapter_score(user, paragraph)
            print("robot %s read book %s chapter %s interest score is %s" % (
                book.book_def.bid,
                user.robot_def.uid,
                idx,
                score
            ))
