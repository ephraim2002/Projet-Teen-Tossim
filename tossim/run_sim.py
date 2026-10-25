#!/usr/bin/env python2
"""Build and run the TEEN TinyOS application in TOSSIM."""
from __future__ import print_function

import argparse
import csv
import math
import os
import re
import subprocess
import sys
import time


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.join(ROOT, "tossim", "teen")
RESULTS_DIR = os.path.join(ROOT, "results")
TOSROOT = os.environ.get("TOSROOT", "/opt/tinyos-main")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from gen_topology import generate as make_topology


def write_topology_header(positions, rounds):
    header = os.path.join(APP_DIR, "Topology.h")
    with open(header, "w") as output:
        output.write("#define TEEN_NODE_COUNT %d\n" % len(positions))
        output.write("#define TEEN_ROUNDS %d\n" % rounds)
        for axis, index in (("X", 0), ("Y", 1)):
            values = ", ".join("%.2ff" % point[index] for point in positions)
            output.write("static const float TEEN_%s[TEEN_NODE_COUNT] = {%s};\n"
                         % (axis, values))
    return header


def parse_log(log_path, nodes, rounds):
    energy = {}
    sent = [0] * (rounds + 1)
    received = [0] * (rounds + 1)
    setup = [0] * (rounds + 1)
    energy_pattern = re.compile(r"ENERGY\s+(\d+)\s+(\d+)\s+(\d+)")
    sent_pattern = re.compile(r"SENT\s+(\d+)")
    received_pattern = re.compile(r"RECEIVED\s+(\d+)\s+(\d+)")
    setup_pattern = re.compile(r"CTRL\s+(\d+)\s+([234])")

    with open(log_path, "r") as source:
        for line in source:
            match = energy_pattern.search(line)
            if match:
                round_number, node_id, nano_joules = [int(v) for v in match.groups()]
                energy.setdefault(round_number, {})[node_id] = nano_joules
                continue
            match = sent_pattern.search(line)
            if match:
                sent[int(match.group(1))] += 1
                continue
            match = received_pattern.search(line)
            if match:
                round_number, count = [int(v) for v in match.groups()]
                received[round_number] += count
                continue
            match = setup_pattern.search(line)
            if match:
                setup[int(match.group(1))] += 1

    expected_nodes = set(range(nodes + 1))
    rows = []
    for round_number in range(1, rounds + 1):
        readings = energy.get(round_number, {})
        if set(readings) != expected_nodes:
            missing = sorted(expected_nodes - set(readings))
            raise RuntimeError("Incomplete energy snapshot at round %d; missing nodes: %s"
                               % (round_number, missing[:10]))
        rows.append((round_number, sum(readings.values()) / 1e9,
                     sent[round_number], received[round_number],
                     setup[round_number]))
    return rows


def run_one(nodes, rounds, seed):
    if nodes < 1 or rounds < 1:
        raise ValueError("nodes and rounds must be positive")
    if not os.path.isdir(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    positions = make_topology(nodes, seed)
    topology_path = os.path.join(ROOT, "tossim", "topology_%d.txt" % nodes)
    with open(topology_path, "w") as topology:
        for node_id, point in enumerate(positions):
            topology.write("%d %.2f %.2f\n" % (node_id, point[0], point[1]))
    write_topology_header(positions, rounds)

    build_environment = os.environ.copy()
    build_environment["TINYOS_ROOT_DIR"] = TOSROOT
    build_environment["TINYOS_MAKE_DIR"] = os.path.join(
        TOSROOT, "support", "make")
    build_environment["TINYOS_OS_DIR"] = os.path.join(TOSROOT, "tos")
    python_sdk = os.path.join(TOSROOT, "support", "sdk", "python")
    build_environment["PYTHONPATH"] = python_sdk + os.pathsep + \
        build_environment.get("PYTHONPATH", "")
    subprocess.check_call(["make", "micaz", "sim"], cwd=APP_DIR,
                          env=build_environment)

    sys.path.insert(0, APP_DIR)
    from TOSSIM import Tossim
    print("Loaded the TOSSIM bindings.")
    sys.stdout.flush()

    log_path = os.path.join(RESULTS_DIR, "tossim_teen_%d.log" % nodes)
    csv_path = os.path.join(RESULTS_DIR, "tossim_teen_%d.csv" % nodes)
    tossim = Tossim([])
    radio = tossim.radio()

    for source in range(nodes + 1):
        for destination in range(nodes + 1):
            if source == destination:
                continue
            dx = positions[source][0] - positions[destination][0]
            dy = positions[source][1] - positions[destination][1]
            distance = max(1.0, math.sqrt(dx * dx + dy * dy))
            radio.add(source, destination, -30.0 - 20.0 * math.log10(distance))

        mote = tossim.getNode(source)
        # TOSSIM's noise model needs at least 20 history readings.
        for unused in range(100):
            mote.addNoiseTraceReading(-105)
        mote.createNoiseModel()
        mote.bootAtTime(1)
    print("Configured %d motes and their radio links." % (nodes + 1))
    sys.stdout.flush()

    started = time.time()
    print("Running %d simulated rounds..." % rounds)
    sys.stdout.flush()
    events = 0
    end_time = (rounds * 5000 + 4900) * tossim.ticksPerSecond() / 1000
    with open(log_path, "w") as log_output:
        tossim.addChannel("TEEN", log_output)
        while tossim.time() < end_time and tossim.runNextEvent():
            events += 1
            if events % 10000 == 0:
                print("Processed %d simulator events." % events)
                sys.stdout.flush()
    elapsed = time.time() - started

    rows = parse_log(log_path, nodes, rounds)
    with open(csv_path, "w") as output:
        writer = csv.writer(output)
        writer.writerow(["round", "residual_energy", "sent", "received",
                         "setup_msgs"])
        writer.writerows(rows)

    sent_total = sum(row[2] for row in rows)
    received_total = sum(row[3] for row in rows)
    pdr = float(received_total) / sent_total if sent_total else 0.0
    print("TEEN/TOSSIM nodes=%d rounds=%d seed=%d pdr=%.3f "
          "sent=%d received=%d avg_setup_msgs=%.1f "
          "wall_seconds=%.2f csv=%s" %
          (nodes, rounds, seed, pdr, sent_total, received_total,
           sum(row[4] for row in rows) / float(rounds), elapsed, csv_path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nodes", type=int, default=100)
    parser.add_argument("--rounds", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--all-sizes", action="store_true",
                        help="run the required 50, 100 and 300 node scenarios")
    parser.add_argument("--worker", action="store_true",
                        help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args.all_sizes and not args.worker:
        for nodes in (50, 100, 300):
            command = [sys.executable, os.path.abspath(__file__), "--worker",
                       "--nodes", str(nodes), "--rounds", str(args.rounds),
                       "--seed", str(args.seed)]
            subprocess.check_call(command)
    else:
        run_one(args.nodes, args.rounds, args.seed)


if __name__ == "__main__":
    main()
