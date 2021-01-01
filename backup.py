import os
import sys
import random
import collections
import logging
import numpy as np
from novel_helper import NovelHelper, S
from args import Args

from event_manager import EventManager
from robot import RobotUser, RobotStatus

"""状态机直观思考：
为什么要用状态机的思维？因为Robot的推荐没有必要完全仿真人类，而状态机易于将问题清晰的描述清楚。
最不应该的就是推翻状态机，再另起炉灶，这套东西虽然不够perfect也不够优美，但是能work能运转。
状态机的思路，和那个叮当猫大富翁有点像，这一回合，你要么扔骰子，要么用道具，要么去发动角色技能，
但是你不能把这些混合在一起。每个status只干一件事。
有点像算子吧。

另外，recommend_novel_to_robot这个项目的目的不是项目本身，而是写文档和博客
"""

class Book:
    def __init__(self, book_def):
        self._book_def = book_def
        self._book_id = book_def.bid


# 上瘾度更新类型
class AddictUpdateType:
    CHAPTER = 0
    CLICK = 1
    DETEST = 2 # 每个period会随机下降一个值
    OFFLINE = 3 # 离线用户会随机以一个速率增长addict_value
    # 用户不会彻底的流失，无非是回撤的这个速率比较慢罢了


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

# 在其他文件里继承该类
class RecommendSysBase(object):
    def __init__(self, action_machine):
        self.action_machine = action_machine
    
    # 直接修改robot_user.choosing_bid_list
    def recommend(self, robot_user, k=8):
        raise NotImplementedError

# 内置的推荐系统会随机返回Book
class RecommendSysBuiltin(RecommendSysBase):
    def __init__(self, action_machine):
        super().__init__(action_machine)

    # 随机推荐k个
    def recommend(self, robot_user, k=8):
        bid_list = list(self.action_machine.book_map.keys())
        k = min(k, len(bid_list))
        bid_recommend_list = random.sample(bid_list, k)
        robot_user._choosing_bid_list.clear()
        for bid in bid_recommend_list:
            robot_user._choosing_bid_list.append(bid)

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

        self.recommend_sys = RecommendSysBuiltin(self)

        self.event_manager = EventManager(self)
        self.event_manager.clean_all_csv()
        
    
    def get_period(self):
        return self._period

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

    # 因为wv_word_idx_map里的key是word2vec产生的，所以有的词是没有的，要过滤掉
    def _fill_no_title(self, word_list):
        new_word_list = []
        for word in word_list:
            if word in self.nh.wv_word_idx_map:
                new_word_list.append(word)
        if not len(new_word_list):
            return ['no', 'title']
        return new_word_list

    def _fill_empty_word_list(self, word_list):
        word_list = [
            word for word in word_list if word in self.novel_helper.wv_word_idx_map
        ]
        if not word_list:
            word_list = ['empty', 'word', 'list']
        return word_list

    def judge_robot_click_book(self, robot_user, book): 
        score = self._get_robot_click_book_score(robot_user, book)
        if score > Args.ub_dot_threshold_alpha:
                return True
        return False
    
    # 统计查询，会先检查sqlite-in-memory的建表状态
    def query(self, sql_text, reprepare=True):
        r = self.event_manager.query(sql_text, reprepare)
        return r

    # 更新用户的addict_value
    def update_addict_value(self, robot_user, update_type, score):
        if random.random() < Args.clean_addict_value_rate:
            robot_user.addict_value = -random.random()
            return
        if update_type == AddictUpdateType.CLICK:
            robot_user.addict_value += score
        elif update_type == AddictUpdateType.CHAPTER:
            robot_user.addict_value += score
        elif update_type == AddictUpdateType.DETEST:
            robot_user.addict_value -= random.random() * Args.addict_value_detest_rate
        elif update_type == AddictUpdateType.OFFLINE:
            robot_user.addict_value += robot_user.addict_value_restore_rate

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
        to_read_paragraph = book.paragraph[chapter-1]
        paragraph_word_list = S.paragraph_to_string_list(to_read_paragraph)
        detest_drive_score = self._dot_robot_book(
            robot_detest_word_list, paragraph_word_list, sample_loop=sample_loop)
        return detest_drive_score

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

    def _get_normal_noise(self, noise_range=1.):
        return noise_range * random.gauss(0., 1.)
    
    def _drive_click(self, robot_user, book):
        drive_success = False
        click_drive_score = self._get_click_drive_score(robot_user, book)
        click_drive_score += self._get_normal_noise(0.1)
        if click_drive_score > Args.click_drive_threshold:
            drive_success = True
        return (drive_success, click_drive_score)
    
    def _drive_read(self, robot_user, book, chapter):
        drive_success = False
        read_drive_score = self._get_read_drive_score(robot_user, book, chapter)
        read_drive_score += self._get_normal_noise(0.1)
        if read_drive_score > Args.read_drive_threshold:
            drive_success = True
        addict_drive_score = self._get_addict_drive_score(robot_user, book, chapter)
        robot_user.addict_value += (addict_drive_score - 0.05)
        return (drive_success, read_drive_score, addict_drive_score)
    
    def _drive_detest(self, robot_user, book, chapter=0):
        drive_success = False
        if chapter == 0:
            detest_drive_score = self._get_title_detest_drive_score(robot_user, book)
        else:
            detest_drive_score = self._get_detest_drive_score(robot_user, book)
        detest_drive_score += self._get_normal_noise(0.1)
        if detest_drive_score > Args.detest_drive_threshold:
            drive_success = True
        robot_user.detest_value += (detest_drive_score - 0.05)
        return (drive_success, detest_drive_score, robot_user.detest_value)
    
    # 判断机器人是否会（继续）使用app
    def _drive_use_app(self, robot_user):
        use_app = False
        addict_value = robot_uesr.addict_value
        detest_value = robot_user.detest_value
        addict_value += self._get_normal_noise(0.1)
        detest_value += self._get_normal_noise(0.1)
        if addict_value > 0 and detest_value < 0:
            use_app = True
        return (use_app, addict_value, detest_value)

    def judge_robot_finish_chapter(self, robot_user, paragraph):
        score = self._get_robot_finish_chapter_score(robot_user, paragraph)
        if score > Args.ub_dot_chapter_finish_threshold_alpha:
            return True
        return False

    # 驱动分值：读完一章
    def _get_robot_finish_chapter_score(self, robot_user, paragraph):
        paragraph_word_list = S.paragraph_to_string_list(paragraph)
        paragraph_word_list = S.lower_string_list(paragraph_word_list)
        book_word_list = self._fill_no_title(paragraph_word_list)
        user_word_list = [ei.word for ei in robot_user.robot_def.ei]
        book_vector = self._word_list_vector_pooling(book_word_list)
        user_vector = self._word_list_vector_pooling(user_word_list)
        score_sum = np.dot(book_vector, user_vector)
        score = score_sum / (len(book_word_list) * len(user_word_list))
        return score

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
        logging.error(report_message)
        # self.metrics_writer.record_action_machine()

    # 在关闭app时做的收尾工作
    def _just_shut_down_app(self, robot_user):
        robot_user._addict_value -= 0.5

    # 更新_addict_value恢复速率
    def _update_addict_value_restore_rate(self, robot_user):
        self._addict_value_restore_rate = self._addict_value_restore_rate

    # # offline状态
    # def _run_robot_offline(self, robot_user):
    #     robot_user._addict_value += robot_user._addict_value_restore_rate
    #     addict_value = robot_user._addict_value
    #     if addict_value > 0:
    #         robot_user._status = RobotStatus.RECOMMEND
        


    # def _run_robot_choosing(self, robot_user):
    #     self.update_addict_value(robot_user, AddictUpdateType.DETEST, 0)
    #     robot_user.choosing_delay -= 1
    #     if robot_user.choosing_delay > 0:
    #         robot_user.status = RobotStatus.CHOOSING
    #     else:
    #         robot_user.status = RobotStatus.CLICK_DRIVE

    # def _run_robot_click_drive(self, robot_user):
    #     # 生成机器人的点击驱动分数，判断是否会发生点击行为
    #     for bid in robot_user.choosing_bid_list:
    #         # 该刷已经点过的book_id，断不会再点
    #         if bid in robot_user.chosen_bid_set:
    #             continue
    #         # 之前展现过，但没点击过的，不会再点（todo: 软性降权，而不是直接不点）
    #         if bid in robot_user.history_impr_map:
    #             continue
    #         book = self.book_map[bid]
    #         click_score = self._get_robot_click_book_score(robot_user, book)
    #         self.update_addict_value(robot_user, AddictUpdateType.CLICK, click_score)
    #         if click_score >= Args.ub_dot_threshold_alpha:
    #             self.event_manager.emit_one_event(uid=robot_user.uid, bid=bid, event='go_detail')
    #             robot_user.reading_bid = bid
    #             robot_user.chosen_bid_set.add(bid)
    #             break
    #     if robot_user.reading_bid is not None:
    #         robot_user.status = RobotStatus.READING
    #     elif self.get_addict_value(robot_user) > 0:
    #         # 如果多次执行到这里，那就是所谓的`狂刷`
    #         robot_user.status = RobotStatus.RECOMMEND
    #     else:
    #         # 执行到这里代表推荐的不好，用户关app了
    #         robot_user.status = RobotStatus.OFFLINE

    # def _run_robot_read_drive(self, robot_user):
    #     read_drive_score = random.random()
    #     drive_chapter = robot_user.reading_chapter + 1
    #     # todo drive_chapter calc
    #     if read_drive_score < 0.1:
    #         robot_user.reading_chapter += 1
    #         robot_user.status = RobotStatus.READING
    #         robot_user.chapter_finish_delay = 3
    #     else:
    #         # 返回列表页选择
    #         robot_user.status = RobotStatus.CLICK_DRIVE


    # def _run_robot_reading(self, robot_user):
    #     self.update_addict_value(robot_user, AddictUpdateType.DETEST, 0)
    #     robot_user.chapter_finish_delay -= 1
    #     if robot_user.chapter_finish_delay <= 0:
    #         robot_user.status = RobotStatus.READ_DRIVE
    #     else:
    #         robot_user.status = RobotStatus.READING
    #     return

    # # 获取用户热情度，用来决定是否继续使用产品
    # def get_addict_value(self, robot_user):
    #     return robot_user.addict_value

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
    
    def _update_use_app_impulse_value(self, robot_user):
        for bid, reading_info in robot_user._history_read_map.items():
            bid_addict_value = reading_info.addict_value
            # 尚未想好bid_addict_value怎么影响_use_app_impulse_value
        delta = (robot_user._addict_rate - robot_user._detest_rate) * 1.
        robot_user._use_app_impulse_value += delta


    def _run_robot_offline(self, robot_user):
        if robot_user._use_app_impulse_value > 0:
            robot_user._status = RobotStatus.RECOMMEND
        else:
            robot_user._status = RobotStatus.OFFLINE
        self._update_use_app_impulse_value(robot_user)
        self._update_addict_rate(robot_user)
        self._update_detest_rate(robot_user)
    
    def _run_robot_recommend(self, robot_user):
        self.recommend_sys.recommend(robot_user)
        robot_user._chosen_bid_set.clear()
        robot_user._choosing_delay = 2
        robot_user._reading_bid = None
        robot_user._status = RobotStatus.CHOOSING
        for bid in robot_user._choosing_bid_list:
            self.event_manager.emit_one_event(uid=robot_user.uid, bid=bid, event='impression')

    def _run_robot_choosing(self, robot_user):
        if robot_user._choosing_delay > 0:
            robot_user._status = RobotStatus.CHOOSING
        else:
            robot_user._status = RobotStatus.CLICK_DRIVE
        robot_user._choosing_delay -= 1
    
    def _run_robot_click_drive(self, robot_user):
        for bid in robot_user._choosing_bid_list:
            if bid in robot_user._chosen_bid_set:
                continue
            book = self.book_map[bid]
            click_drive_score = self._get_click_drive_score(
                robot_user, book, sample_loop=1)
            if bid in robot_user._history_impr_map:
                suppress_rate = .5
            else:
                suppress_rate = 1.
            # sys.stdout.write("\r %s" % click_drive_score)
            click_drive_score *= suppress_rate
            if click_drive_score > Args.click_drive_threshold:
                robot_user._reading_bid = bid
                robot_user._chosen_bid_set.add(bid)
                robot_user._history_read_map[bid] = ReadingInfo(
                    last_period=self._period,
                    chapter=0,
                    addict_value=0)
                break
            if random.random() < 0.1: # 10%的概率会被机器人记住“给我推过了”
                robot_user._history_impr_map[bid] = ImpressionInfo(last_period=self._period)
        if robot_user._reading_bid:
            robot_user._status = RobotStatus.READ_DRIVE
        else:
            # todo: not only OFFLINE, but also RECOMMEND
            robot_user._status = RobotStatus.OFFLINE

    # chapter记录的是之前读完哪一章了，之后从下一章开始读
    def _run_robot_read_drive(self, robot_user):
        robot_user._status = RobotStatus.OFFLINE
        bid = robot_user._reading_bid
        book = self.book_map[bid]
        reading_info = robot_user._history_read_map[bid]
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
        if read_drive_score > Args.read_drive_threshold:
            robot_user._status = RobotStatus.READING
            robot_user._chapter_finish_delay = 3
        else:
            robot_user._status = RobotStatus.CHOOSING

    def _run_robot_reading(self, robot_user):
        if robot_user._chapter_finish_delay > 0:
            robot_user._status = RobotStatus.READING
            robot_user._chapter_finish_delay -= 1
        else:
            robot_user._status = RobotStatus.READ_DRIVE


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

    def run(self, k=Args.period_threshold):
        self._period = 0
        while self._period+1 <= k:
            self.run_one_period()

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
