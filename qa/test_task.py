# @Date  : 2021/3/19
# @Author: Hugh
# @Email : 609799548@qq.com

import os
import sys
import argparse
import importlib
from datetime import datetime

from .config import Config
from .common import Path, DB, ExcelDataHandler, run_testcase, generate_testcase, format_main, format_print


class TestTask:

    def __init__(self, config_path):
        self.config = Config(config_path)
        self.project_path = os.path.dirname(config_path)

    @property
    def fixture_module(self):
        try:
            if not self.config.fixture:
                return
            sys.path.append(self.project_path)
            return importlib.import_module(f'scripts.{self.config.fixture[:-3]}')
        except ModuleNotFoundError:
            print(f'请检查:{self.config.path} fixture: {self.config.fixture} 是否存在')
            raise

    @property
    def setup(self):
        return getattr(self.fixture_module, 'setup', None)

    @property
    def teardown(self):
        return getattr(self.fixture_module, 'teardown', None)

    def run(self):
        start_time = datetime.now()
        json_name = 'debug' if self.config.debug else start_time.timestamp()
        path = Path(self.project_path)
        temp_json = DB(os.path.join(path.temp, f'{self.config.meta.title}_{json_name}.json'))

        info = dict(start_time=start_time, path=path, config=self.config)

        # 测试任务 setup
        setup = self.setup
        format_main('setup')
        format_print('setup', setup.__doc__)
        if callable(setup):
            setup_result = setup()
            if isinstance(setup_result, dict):
                for key, value in setup_result.items():
                    temp_json.set(key, value)

        if self.config.config_files:
            testcases = []
            for config_path in self.config.config_files:
                _config = Config(os.path.join(path.project_path, config_path))
                testcases.append(generate_testcase({
                    'config': _config,
                    'excel_data': ExcelDataHandler.run(path, _config.excel_files),
                    'db': temp_json,
                    'fixture': self.fixture_module,
                    'path': path
                }))
            run_testcase(*testcases, info=info)

        else:
            # 1. 获取 excel 数据
            excel_data = ExcelDataHandler.run(path, self.config.excel_files)

            # 2. 生成 unittest 测试用例，并执行
            run_testcase(generate_testcase({
                'config': self.config,
                'excel_data': excel_data,
                'db': temp_json,
                'fixture': self.fixture_module,
                'path': path
            }), info=info)

        # 测试任务 teardown
        teardown = self.teardown
        format_main('teardown', pre='\n')
        format_print('teardown', teardown.__doc__)
        if callable(teardown):
            teardown()

    def get_excel_data(self):
        if self.config.config_files:
            for config_path in self.config.config_files:
                _config = Config(config_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', required=True)
    config = parser.parse_args().config
    TestTask(config).run()