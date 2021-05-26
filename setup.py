import setuptools

from distutils.core import setup


setup(
    name='qa',
    version='0.0.1',
    author='丘家劲',
    author_email='609799548@qq.com',
    description='接口自动化测试',
    package_data={
        '': ['resources\*']
    },
    entry_points={
        'console_scripts': [
            'qa=qa:main'
        ]
    },
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'certifi==2020.12.5',
        'chardet==4.0.0',
        'et-xmlfile==1.0.1',
        'idna==2.10',
        'jsonpath==0.82',
        'openpyxl==3.0.7',
        'PyMySQL==1.0.2',
        'requests==2.25.1',
        'urllib3==1.26.4',
        'oss2==2.14.0'
    ]
)


# python3 setup.py sdist bdist_wheel
