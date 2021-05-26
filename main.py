# @Date  : 2021/3/29
# @Author: Hugh
# @Email : 609799548@qq.com

import argparse

from qa.test_task import TestTask
from qa.command_line import mkdir


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config')
    parser.add_argument('-m', '--make')
    namespace = parser.parse_args()
    config, make = namespace.config, namespace.make
    if config:
        TestTask(config).run()
    elif make:
        mkdir(make)

    # python main.py -c test.config.json
    # python main.py -c init.config.json

