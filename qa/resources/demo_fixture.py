

def setup():
    """
    测试开始之前的setup操作
    return 的 dict 会被 insert 到 temp.json 中，后续可以通过 ${}方式引用
    """
    print('project setup')
    return {}


def teardown():
    """测试结束之后的teardown操作"""
    print('project teardown')

