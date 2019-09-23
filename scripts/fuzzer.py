#!/usr/bin/env python
# -*- coding: utf-8 -*-

import arrow
import random
import os
import sys

from watson import Watson

FUZZER_PROJECTS = [
    ("apollo11", ["reactor", "module", "wheels", "steering", "brakes"]),
    ("hubble", ["lens", "camera", "transmission"]),
    ("voyager1", ["probe", "generators", "sensors", "antenna"]),
    ("voyager2", ["probe", "generators", "sensors", "antenna"]),
]


def get_config_dir():
    if len(sys.argv) == 2:
        if not os.path.isdir(sys.argv[1]):
            sys.exit("Invalid directory argument")
        return sys.argv[1]
    elif os.environ.get('WATSON_DIR'):
        return os.environ.get('WATSON_DIR')
    else:
        sys.exit(
            "This script will corrupt Watson's data, please set the WATSON_DIR"
            " environment variable to safely use it for development purpose."
        )


def fill_watson_randomly(watson, project_data):
    now = arrow.now()

    for date in arrow.Arrow.range('day', now.shift(months=-1), now):
        if date.weekday() in (5, 6):
            # Weekend \o/
            continue

        start = date.replace(hour=9, minute=random.randint(0, 59)) \
                    .shift(seconds=random.randint(0, 59))

        while start.hour < random.randint(16, 19):
            project, tags = random.choice(project_data)
            frame = watson.frames.add(
                project,
                start,
                start.shift(seconds=random.randint(60, 4 * 60 * 60)),
                tags=random.sample(tags, random.randint(0, len(tags)))
            )
            start = frame.stop.shift(seconds=random.randint(0, 1 * 60 * 60))


if __name__ == '__main__':
    config_dir = get_config_dir()
    watson = Watson(config_dir=config_dir, frames=None, current=None)
    fill_watson_randomly(watson, FUZZER_PROJECTS)
    watson.save()
