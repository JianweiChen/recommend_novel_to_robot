# coding=utf8
from rec_sys.base_rec_sys import BaseRecSys

#这个东西会根据Book包含的word和Robot的ei来推荐
# 属于hack整个系统，为的就是测试出整个系统的最优天花板
class HackRecSys(BaseRecSys):
    def __init__(self, action_service):
        super().__init__(action_service)