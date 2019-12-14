import os
import random
from typing import List

lines: List[str] = []


def get_triplets(count: int = 1000):
    global lines
    if len(lines) == 0:
        with open('data/triplets.txt') as triplets_file:
            for line in triplets_file:
                lines.append(line)

    triplets = []
    for line in random.sample(lines, count):
        names = line.strip('\n').split(' ')
        t = [os.path.join('static/images', n + '.jpg') for n in names]
        triplets.append(t)

    return triplets
