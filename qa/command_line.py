# @Date  : 2021/3/22
# @Author: Hugh
# @Email : 609799548@qq.com

import os
import sys
import json
import copy
import shutil

from .test_task import TestTask
from .common import format_main, format_print


config_template = {
    "meta": {
        "title": "",
        "description": "",
        "tester": "Robot"
    },
    "excel_files": [
        {
            "name": "示例.xlsx",
            "order": ['Sheet1']
        }
    ],
    "fixture": "fixture.py",
    "database": {},
    "http": {
        "base_url": "https://httpbin.org",
        "prefix": "",
        "timeout": 1,
        "headers": {
            "Content-Type": "application/json"
        },
        "expect": {
            "status_code": 200
        }
    },
    "email": {},
    "debug": False,
    "auto": {
        "web_hook": ""
    }
}


def _mkdir(*paths):
    for path in paths:
        os.mkdir(path)


def mkdir(name):
    project_path = os.path.join(os.getcwd(), name)
    report_path = os.path.join(project_path, 'report')
    scripts_path = os.path.join(project_path, 'scripts')
    testcase_path = os.path.join(project_path, 'testcase')
    temp_path = os.path.join(project_path, 'temp')

    base_path = os.path.dirname(os.path.abspath(__file__))
    resources_path = os.path.join(base_path, 'resources')

    target_excel_path = os.path.join(testcase_path, '示例.xlsx')
    raw_excel_path = os.path.join(resources_path, '示例.xlsx')

    target_script_path = os.path.join(scripts_path, 'fixture.py')
    raw_script_path = os.path.join(resources_path, 'demo_fixture.py')

    config_path = os.path.join(project_path, 'init.config.json')
    config = copy.deepcopy(config_template)
    config['meta'].update({'title': name + '测试', 'description': name + '测试描述'})

    format_print('create project name', name)
    format_print('create project path', project_path)

    _mkdir(project_path, testcase_path, report_path, temp_path, scripts_path)
    shutil.copy(raw_excel_path, target_excel_path)
    shutil.copy(raw_script_path, target_script_path)
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def run(config_name):
    format_main('run test', pre='')
    project_path = os.getcwd()
    config_path = os.path.join(project_path, config_name)
    format_print('project path', project_path)
    format_print('config path', config_path)
    TestTask(config_path).run()


def main():
    argv = sys.argv
    if len(argv) < 3:
        return
    command = argv[1]
    arg = argv[2]

    func = globals().get(command)
    if func and arg:
        func(arg)


if __name__ == '__main__':
    main()
