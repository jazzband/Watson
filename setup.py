from setuptools import setup

setup(
    name='watson',
    version='0.1',
    packages=['watson'],
    install_requires=[
        'Click',
        'arrow',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'watson = watson.__main__:cli',
        ]
    }
)
