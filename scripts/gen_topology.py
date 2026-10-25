"""Generate positions for a base station and N random sensors."""
from __future__ import print_function

import random
import sys


def generate(nodes, seed=1):
    if nodes < 1:
        raise ValueError("nodes must be positive")
    rng = random.Random(seed)
    positions = [(100.0, 250.0)]
    for unused in range(nodes):
        positions.append((round(rng.uniform(0, 200), 2),
                          round(rng.uniform(0, 200), 2)))
    return positions


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: gen_topology.py N [seed]")
    nodes = int(sys.argv[1])
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    for node_id, point in enumerate(generate(nodes, seed)):
        print(node_id, point[0], point[1])


if __name__ == "__main__":
    main()
