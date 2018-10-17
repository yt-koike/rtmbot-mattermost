#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='rtmbot-mattermost',
    version='0.5.2',
    description='A Mattermost bot written in python that connects via the RTM API.',
    author='ShotaKitazawa',
    author_email='skitazawa1121@gmail.com',
    url='https://github.com/ShotaKitazawa/rtmbot-mattermost',
    packages=find_packages(),
    entry_points={'console_scripts': ['rtmbot-mattermost=rtmbot_mattermost.bin.run_rtmbot:main']},
    install_requires=[
        'pyyaml>=3, <4',
        'mattermostdriver>=6'
    ]
)
