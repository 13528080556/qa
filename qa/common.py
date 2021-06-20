# @Date  : 2021/3/19
# @Author: Hugh
# @Email : 609799548@qq.com

import os
import re
import ast
import copy
import json
import unittest
from urllib.parse import urljoin

import requests
import jsonpath

from .ddt import ddt, data
from .work_robot import WxWork
from .HTMLTestRunner import HTMLTestRunner
from .operation_excel import OperationExcel, Header
from .dependent_handler import DependentHandler


class Path:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self, project_path):
        self.project_path = project_path

    def _mkdir(self, name):
        _path = os.path.join(self.project_path, name)
        if not os.path.exists(_path):
            os.mkdir(_path)
        return _path

    @property
    def report(self):
        return self._mkdir('report')

    @property
    def testcase(self):
        return self._mkdir('testcase')

    @property
    def temp(self):
        return self._mkdir('temp')

    @property
    def scripts(self):
        return self._mkdir('scripts')

    @property
    def resource(self):
        return self._mkdir('resource')


class DB:
    def __init__(self, path):
        self.path = path
        self.encoding = 'utf-8'
        with open(self.path, 'w', encoding=self.encoding) as f:
            json.dump({}, f, indent=2, ensure_ascii=False)

    @property
    def data(self):
        with open(self.path, 'r', encoding=self.encoding) as f:
            return json.loads(f.read())

    def get(self, keyword):
        return self.data[keyword]

    def set(self, keyword, value):
        raw_data = self.data
        raw_data.update({keyword: value})
        with open(self.path, 'w', encoding=self.encoding) as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)

    def __getitem__(self, item):
        return self.get(item)

    def __str__(self):
        return str(self.data)


def generate_testcase(task):
    @ddt
    class TestCase(unittest.TestCase):

        config = task['config']
        db = task['db']
        fixture = task['fixture']
        path = task['path']

        @data(*task['excel_data'])
        def test_(self, case_data):
            # 获取实例化 case, 可以通过 case.属性 获取响应的值
            case = RequestDataFormatter(case_data, self.config, self.db)
            case.path = self.path
            log_excel(case_data)

            if case.setup:
                name, args = CaseFixtureFormat.get_func_name_args(case.setup, case)
                format_print('Case Setup', name, args, pre='\n')
                func_result = getattr(self.fixture, name)(*args)
                if isinstance(func_result, dict):
                    for k, v in func_result.items():
                        self.db.set(k, v)
                        format_print('Case Setup Insert', f'Key: {k}, Value: {v}')

            timeout = case.timeout or self.config.http.timeout
            try:
                response = requests.request(case.method, case.url, headers=case.headers,
                                            data=case.data.encode('utf-8').decode('latin1'), timeout=timeout)
            except Exception as e:
                if isinstance(e, requests.exceptions.ReadTimeout):
                    print(f'【异常】请求超时，该用例测试超时时间为 {timeout}')
                raise e
            else:
                log_request(response, timeout)
                self._assert(case.expect, response)  # 断言
                self._extract(case.extract, response)  # 提取数据
                case.response = response  # 给 case 对象绑定响应

            # TODO 数据库校验
            print('case: teardown:', case.teardown)
            if case.teardown:
                name, args = CaseFixtureFormat.get_func_name_args(case.teardown, case)
                format_print('Case TearDown', name, args, pre='\n')
                getattr(self.fixture, name)(*args)

        def _assert(self, case_expect, response):
            if 'status_code' in case_expect:
                self.assertEqual(case_expect['status_code'], response.status_code)

            for key, value in case_expect.get('response', {}).items():
                json_data = response.json()
                actual_result = jsonpath.jsonpath(json_data, key)
                if actual_result is False:
                    raise ValueError('not found <jsonpath: {}, response: {}>'.format(key, json_data))
                self.assertEqual(value, actual_result[0])

        def _extract(self, extract, response):
            for key, value in extract.items():
                extract_data = jsonpath.jsonpath(response.json(), value)
                if extract_data:
                    self.db.set(key, extract_data[0])

    return TestCase


def run_testcase(*testcase, info):
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for _case in testcase:
        suite.addTest(loader.loadTestsFromTestCase(_case))

    start_time, path, config = info['start_time'], info['path'], info['config']

    report_name = f'{start_time.strftime("%y%m%d%H%M%S")}.html'
    report_path = path.report
    if config.debug:
        report_name = f'{config.meta.title}-debug.html'
    if config.auto:
        report_name = f'{config.meta.title}.html'
    report_path = os.path.join(report_path, report_name)
    format_main('start test')
    with open(report_path, 'wb') as f:
        runner = HTMLTestRunner(stream=f, title=config.meta.title,
                                description=config.meta.description, tester=config.meta.tester)
        runner.run(suite)
    format_print('report path:', report_path, pre='\n')
    if config.auto:
        web_hook = config.auto.get('web_hook')
        if web_hook and config.auto.get('send') == 'y':
            robot = WxWork(web_hook)
            robot.send_file(robot.upload(report_path))


class RequestDataFormatter:
    https_re = re.compile('^https?://.+')
    dependent_handler = DependentHandler()

    def __init__(self, excel_data, config, db):
        self.excel_data = excel_data
        self.config = config  # config 配置信息
        self.db = db

    @property
    def title(self):
        return self.excel_data[Header.CASE_TITLE]

    @property
    def url(self):
        """
        获取经过依赖替换以及拼接 Host、prefix 的 URL
        """
        path = self.dependent_handler(self.excel_data[Header.CASE_URL], self.db)
        if self.https_re.match(path):
            return path
        host = self.excel_data.get('inner_config').get('base_url') or self.config.http.base_url
        prefix = self.excel_data.get('inner_config').get('prefix') or self.config.http.prefix
        if prefix.endswith('/'):
            prefix = prefix[:-1]
        if not path.startswith('/'):
            path = '/' + path
        return urljoin(host, prefix + path)

    @property
    def method(self):
        """返回请求方法 str """
        return self.excel_data[Header.CASE_METHOD]

    @property
    def headers(self):
        """返回请求头 dict """
        inner_headers = self.excel_data.get('inner_config').get('headers')
        if inner_headers:
            header = json.loads(inner_headers)
        else:
            header = copy.deepcopy(self.config.http.headers)
        case_header = json.loads(self.dependent_handler(self.excel_data[Header.CASE_HEADER], self.db)) \
            if self.excel_data[Header.CASE_HEADER] else {}
        header.update(case_header)
        return header

    @property
    def data(self):
        """返回请求数据 str """
        return self.dependent_handler(self.excel_data[Header.CASE_DATA], self.db) \
            if self.excel_data[Header.CASE_DATA] else ''

    @property
    def expect(self):
        """返回预期结果  dict """
        expect = self.config.http.expect
        case_expect = json.loads(self.excel_data[Header.CASE_EXPECT]) if self.excel_data[Header.CASE_EXPECT] else {}
        expect.update(case_expect)
        return expect

    @property
    def extract(self):
        """返回提取数据 dict"""
        return json.loads(self.excel_data[Header.CASE_EXTRACT]) if self.excel_data[Header.CASE_EXTRACT] else {}

    @property
    def setup(self):
        """返回用例前置操作 str"""
        return self.excel_data[Header.CASE_SETUP]

    @property
    def teardown(self):
        """返回用例后置操作 str"""
        return self.excel_data[Header.CASE_TEARDOWN]

    @property
    def is_run(self):
        return self.excel_data[Header.CASE_RUN].upper()

    @property
    def timeout(self):
        inner_timeout = self.excel_data.get('inner_config').get('timeout')
        case_timeout = float(self.excel_data[Header.CASE_TIMEOUT]) if self.excel_data[Header.CASE_TIMEOUT] else 0
        global_timeout = self.config.http.timeout or 1
        timeout = case_timeout or inner_timeout or global_timeout
        return timeout

    @property
    def row(self):
        return self.excel_data['EXCEL_ROW']


class ExcelDataHandler:

    @staticmethod
    def get_data(path, excel):
        excel_name = excel if isinstance(excel, str) else excel['name']
        e = OperationExcel(os.path.join(path.testcase, excel_name))
        order = excel.get('order') if isinstance(excel, dict) and excel.get('order') else e.sheet_names
        _data = e.data
        result = []
        for sheet_name in order:
            result.extend(_data[sheet_name])
        return result

    @classmethod
    def run(cls, path, excel_files):
        """遍历 config excel files 并且剔除 不运行的测试用例"""
        result = []
        for excel in excel_files:
            temp = []
            inner_config = OperationExcel(os.path.join(path.testcase, excel['name'])).config_excel_data
            for case in cls.get_data(path, excel):
                if case[Header.CASE_RUN] and case[Header.CASE_RUN].strip().upper() == 'N':
                    continue
                case['inner_config'] = inner_config
                temp.append(case)
            result.extend(temp)
        return result


class CaseFixtureFormat:
    func_args_re = re.compile(r'^([a-zA-Z\\_][0-9a-zA-Z\\_]*)\((.*?)\)$')

    @classmethod
    def get_func_name_args(cls, string, case):
        m = cls.func_args_re.match(string)
        if m:
            func_name = m.group(1)
            if m.group(2) == '':
                func_args = ()
            else:
                args_string = m.group(2)
                try:
                    func_args = ast.literal_eval(args_string)
                    if not isinstance(func_args, tuple):
                        func_args = [func_args]
                    func_args = list(func_args)
                    for index, arg in enumerate(func_args):
                        if arg == '${case}':
                            func_args[index] = case
                except ValueError:
                    raise ValueError('非法 fixture :', string)

            return func_name, func_args
        raise ValueError('非法 fixture :', string)


def format_print(title, *messages, pre=''):
    print(f'{pre}【{title}】: ', *messages)


def format_main(title, count=30, pre='\n'):
    while len(title) < 15:
        title = ' ' + title
        title = title + ' '

    prefix = '*' * count
    if len(title) == 15:
        string = prefix + title + '*' * count
    else:
        string = prefix + title + '*' * (count - 1)
    print(pre + string)


def log_excel(excel_case_data):
    # _headers = list(Header.__members__.values())
    # _body = [excel_case_data[key] for key in _headers]
    # print('body')
    # print(_body)
    print()
    format_print('Excel Row', excel_case_data['EXCEL_ROW'])
    format_print('Excel Title', excel_case_data[Header.CASE_TITLE])
    format_print('Excel Url', excel_case_data[Header.CASE_URL])
    format_print('Excel Method', excel_case_data[Header.CASE_METHOD])
    format_print('Excel Headers', excel_case_data[Header.CASE_HEADER])
    format_print('Excel Data', excel_case_data[Header.CASE_DATA])
    format_print('Excel Setup', excel_case_data[Header.CASE_SETUP])
    format_print('Excel Teardown', excel_case_data[Header.CASE_TEARDOWN])
    format_print('Excel Expect', excel_case_data[Header.CASE_EXPECT])
    format_print('Excel Extract', excel_case_data[Header.CASE_EXTRACT])
    format_print('Excel Timeout', excel_case_data[Header.CASE_TIMEOUT])


def log_request(case_response, timeout):
    _request = case_response.request
    print()
    format_print('Request URL', _request.url)
    format_print('Request Method', _request.method)
    format_print('Request Headers', _request.headers)
    format_print('Request Timeout', timeout)
    if _request.body:
        format_print('Request Data', _request.body.encode('latin1').decode())
    print()
    format_print('Response Status', case_response.status_code)
    format_print('Response Header', case_response.headers)
    format_print('Response Data', case_response.text)
    format_print('用时(s)', case_response.elapsed.total_seconds())


if __name__ == '__main__':
    log_excel('')
