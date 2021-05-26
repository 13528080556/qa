# @Date  : 2021/03/12
# @Author: Hugh
# @Email : 609799548@qq.com

import re


class DependentHandler:
    """依赖处理器"""
    special_characters = r'\^$*+?.()[]'  # 正则元字符需要特殊处理

    def __init__(self, prefix='${', suffix='}'):
        """
        :param prefix: 依赖前缀
        :param suffix: 依赖后缀
        """
        self.original_prefix, self.original_suffix = prefix, suffix
        self._prefix, self._suffix = self._format_prefix_suffix(prefix, suffix)
        self._rule = re.compile(f'{self._prefix}(.+?){self._suffix}')

    def _format(self, string):
        """元字符需要加转义符号 \\"""
        return ''.join(["\\" + char if char in self.special_characters else char for char in string])

    def _format_prefix_suffix(self, prefix, suffix):
        """前缀、后缀都需要检测是否包含元字符"""
        return self._format(prefix), self._format(suffix)

    def __call__(self, data, db):
        """
        处理依赖
        :param data: 包含要替换变量的字符串
        :param db: 拥有要替换后的变量值的 db
        :return:
        """
        dependents = self._rule.findall(data)
        for dependent in dependents:
            data = data.replace(f'{self.original_prefix}%s{self.original_suffix}' % dependent, str(db.get(dependent)))
        return data
