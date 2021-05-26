# @Date  : 2021/3/19
# @Author: Hugh
# @Email : 609799548@qq.com

import json


class Config:

    def __init__(self, path):
        self.path = path
        with open(self.path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    @property
    def meta(self):
        return _MetaConfig(**self.data.get('meta', {}))

    @property
    def excel_files(self):
        return self.data.get('excel_files')

    @property
    def fixture(self):
        return self.data.get('fixture', '')

    @property
    def database(self):
        return self.data.get('database')

    @property
    def http(self):
        return _HttpConfig(**self.data.get('http', {}))

    @property
    def email(self):
        return self.data.get('email')

    @property
    def debug(self):
        return self.data.get('debug')

    @property
    def auto(self):
        return self.data.get('auto')

    def __str__(self):
        return '<Config: %s>' % self.data

    __repr__ = __str__


class _MetaConfig:
    def __init__(self, title=None, description=None, tester=None, **kwargs):
        self.title = title
        self.description = description
        self.tester = tester
        self.kwargs = kwargs


class _HttpConfig:
    def __init__(self, base_url=None, prefix='', timeout=1, headers=None, expect=None, **kwargs):
        self.base_url = base_url
        self.prefix = prefix
        self.timeout = timeout
        self.headers = headers if headers else {}
        self.expect = expect if expect else {}
        self.kwargs = kwargs
