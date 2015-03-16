import arrow
import random

from watson import Watson

watson = Watson(frames=None, current=None)

projects = [
    "apollo11",
    "hubble",
    "voyager1",
    "voyager2",
]

now = arrow.now()

for date in arrow.Arrow.range('day', now.replace(months=-1), now):
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
