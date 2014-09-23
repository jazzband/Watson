from setuptools import setup

setup(
    name='watson',
    version='0.1',
    py_modules=['watson'],
    install_requires=[
        'Click',
        'arrow',
        'requests'
    ],
    entry_points='''
        [console_scripts]
        watson=watson:cli
    ''',
)
