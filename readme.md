# qa 使用

## 创建测试项目
- python main.py -m [测试项目名] example: python main.py -m demo
- qa mkdir [测试项目名] example: qa mkdir demo

## 执行测试
- python main.py -c [配置文件路径]
- qa run [配置文件路径]

## report
生成的测试报告会存放在此处

## scripts
0. 在配置文件中修改 fixture 为对应文件名
1. 测试前后要执行的步骤
   * 测试前置 setup 函数 (该函数如果返回 dict, 会存到缓存，后续可以 ${变量名} 调用)
   * 测试后置 teardown 函数
2. 每个测试用例请求前后的步骤
    * 自定义函数名、函数参数
    * Excel 中填入对应的 函数名(参数1, 参数2)
    * 备注: 测试用例前置返回 dict, 会存到缓存，后续的测试用例，可以通过 ${变量名} 调用
    
## temp
执行测试任务过程中产生的依赖变量

## testcase
存放测试用例

## config.json
- meta
    - title: 测试报告标题 (不要含有下划线、空格)
    - description: 测试报告描述信息
    - tester: 测试报告上的测试人员信息
- excel_files 需要执行的excel文件
    - str: 根据 excel 表里的 Sheet 顺序执行用例
    - dict
        - name: excel 表名
        - order: 根据 order 定义的顺序执行
- fixture: 固件
    - setUp: 测试计划执行前置操作
    - tearDown: 测试计划执行后置操作
- database: 数据库相关配置
- http: 请求相关配置
    - base_url(str): 请求 host
    - prefix(str): 请求 url 前缀
    - timeout(int、float): 超时时间设置
    - headers(dict): 公用 Header 可以配置在这里
    - expect(dict): 通用预期结果配置，通常配置 HTTP 响应码为 200, 如 {"status_code": 200 }
- debug:
    - false(default): 对于同个测试任务，每次测试都会在 temp、report下生成新的文件
    - true: 对于同个测试任务，temp、report下不会生成新文件
- auto:
    - send: y
    - webhook: 企业微信机器人 webHook
    
## excel 文件
请求地址、请求头、请求数据 中可以通过 ${变量名} 的方式引用变量

预期结果采用 jsonpath 的形式，如 {"response": {"$.code": 401, "message": "token错误"}

前置操作、后置操作: 
1. 预先在 fixture 的脚本文件文件中定义好函数
2. 在此处输入 函数名(参数)

提取数据: {"后续引用的变量名": "jsonpath语法"}，如 {"good_id": "$..id"}

是否运行: 默认是运行的状态，此处输入 N 或者 n, 该测试用例将不会执行

超时时间: 单位秒, 可以设置单接口的超时时间
