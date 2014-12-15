from datetime import datetime
from random import randint

from watson import Watson

watson = Watson({})

projects = [
    "apollo11",
    "apollo11/reactor",
    "apollo11/module",
    "apollo11/lander",
    "hubble",
    "voyager1",
    "voyager2",
]

for project in projects:
    for month in range(1, 13):
        for day in range(1, 29):
            if randint(1, 5) != 1:
                start = randint(9, 17)
                stop = start + randint(1, 4)

                watson.frames.add(
                    project,
                    datetime(2014, month, day, start, randint(0, 59)),
                    datetime(2014, month, day, stop, randint(0, 59))
                )

                if stop < 14 and randint(1, 3) == 2:
                    start = stop + randint(1, 3)
                    stop = start + randint(1, 4)

                    watson.frames.add(
                        project,
                        datetime(2014, month, day, start, randint(0, 59)),
                        datetime(2014, month, day, stop, randint(0, 59))
                    )

watson.save()
