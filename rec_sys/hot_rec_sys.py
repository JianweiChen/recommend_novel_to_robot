# coding=utf8
from rec_sys.base_rec_sys import BaseRecSys

# 根据热度来推荐，理论上会提升ctr
class HotRecSys(BaseRecSys):
    def __init__(self, action_service):
        super().__init__(action_service)