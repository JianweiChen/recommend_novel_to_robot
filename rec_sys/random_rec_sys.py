# coding=utf8
import os
import sys
import random
from rec_sys.base_rec_sys import RecSysBase
# 内置的推荐系统会随机返回Book
class RecSysRandom(RecSysBase):
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