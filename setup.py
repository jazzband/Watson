from setuptools import setup

setup(
    name='watson',
    version='0.1',
    packages=['watson', 'gui'],
    install_requires=[
        'Click',
        'arrow',
        'requests',
    ],
    extras_require={
        'gui': ['PySide']
    },
    entry_points={
        'console_scripts': [
            'watson = watson.__main__:cli',
        ],
        'gui_scripts': [
            'watson-systray = gui.__main__:main',
        ]
    }
)
