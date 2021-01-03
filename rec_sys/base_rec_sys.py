# coding=utf8

# 在其他文件里继承该类
class RecSysBase(object):
    def __init__(self, action_machine):
        self.action_machine = action_machine
    
    # 直接修改robot_user.choosing_bid_list
    def recommend(self, robot_user, k=8):
        raise NotImplementedError