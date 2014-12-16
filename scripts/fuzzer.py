import arrow
import random

from watson import Watson

watson = Watson(frames=None, current=None)

projects = [
    "apollo11",
    "apollo11/reactor",
    "apollo11/module",
    "apollo11/lander",
    "apollo11/lander/wheels",
    "apollo11/lander/steering",
    "apollo11/lander/brakes",
    "apollo11/lander/parachute",
    "hubble",
    "hubble/lens",
    "hubble/camera",
    "hubble/transmission",
    "voyager1",
    "voyager1/probe",
    "voyager1/probe/generators",
    "voyager1/probe/sensors",
    "voyager1/probe/antenna",
    "voyager1/launcher",
    "voyager2",
    "voyager2/probe",
    "voyager2/probe/generators",
    "voyager2/probe/sensors",
    "voyager2/probe/antenna",
    "voyager2/launcher",
]

now = arrow.now()

for date in arrow.Arrow.range('day', arrow.get(0), now):
    if date.weekday() in (5, 6):
        # Weekend \o/
        continue

    start = date.replace(
        hour=9, minute=random.randint(0, 59), seconds=random.randint(0, 59)
    )

    while start.hour < random.randint(16, 19):
        frame = watson.frames.add(
            random.choice(projects),
            start,
            start.replace(seconds=random.randint(60, 4 * 60 * 60))
        )
        start = frame.stop.replace(seconds=random.randint(0, 1 * 60 * 60))

watson.save()
