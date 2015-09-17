from setuptools import setup

with open('README.md') as f:
    readme = f.read()


setup(
    name='td-watson',
    version='1.0.1',
    packages=['watson'],
    author='TailorDev',
    author_email='contact@tailordev.com',
    license='MIT',
    long_description=readme,
    install_requires=[
        'Click',
        'arrow',
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'watson = watson.__main__:cli',
        ]
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Customer Service",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "Intended Audience :: Other Audience",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Topic :: Office/Business",
        "Topic :: Utilities",
    ],
    keywords='watson time-tracking time tracking monitoring report',
)
