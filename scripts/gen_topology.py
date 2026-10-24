"""Génère la topologie (id x y) : noeud 0 = BS en (100,250), puis N capteurs sur 200x200.
Usage: python3 gen_topology.py 100 1 > ../tossim/topology_100.txt"""
import random, sys
n = int(sys.argv[1]); seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
r = random.Random(seed)
print(0, 100.0, 250.0)
for i in range(1, n+1):
    print(i, round(r.uniform(0,200),2), round(r.uniform(0,200),2))
