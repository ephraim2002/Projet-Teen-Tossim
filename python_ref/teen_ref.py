"""Simulation de référence TEEN (Python) - mêmes paramètres que le TP.
Sert à : valider le modèle d'énergie, fixer les valeurs attendues, comparer avec TOSSIM.
Usage: python teen_ref.py --nodes 100 --rounds 1000 --seed 1
"""
import argparse, csv, math, random

# --- Modèle radio de premier ordre (imposé par le TP) ---
E_ELEC = 50e-9        # J/bit
E_FS   = 10e-12       # J/bit/m^2
E_MP   = 0.0013e-9    # J/bit/m^4
D0     = math.sqrt(E_FS / E_MP)   # ~2.77 m with the TP's nJ coefficient
PKT, CTRL = 4000, 200            # bits (données / contrôle)

def etx(k, d):
    return E_ELEC*k + (E_FS*k*d*d if d < D0 else E_MP*k*d**4)
def erx(k):
    return E_ELEC*k

def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def run(n=100, rounds=1000, seed=1, p=0.05, e0=0.5, area=200, bs=(100,250),
        ht=30.0, st=2.0, per=0.02, out=None):
    rnd = random.Random(seed)
    pos = [(rnd.uniform(0, area), rnd.uniform(0, area)) for _ in range(n)]
    energy = [e0]*n
    last_ch = [-10**9]*n          # dernier round où le noeud fut CH
    sv = [None]*n                 # Sensed Value (dernière valeur transmise)
    event = None                  # (cx, cy, fin)
    sent = recv = 0
    ctrl_msgs_setup = []
    rows = []
    first_dead = None
    for r in range(rounds):
        alive = [i for i in range(n) if energy[i] > 0]
        if not alive:
            rows.append((r, 0.0, sent, recv, 0)); continue
        # événement physique aléatoire
        if event is None and rnd.random() < 0.03:
            event = (rnd.uniform(0, area), rnd.uniform(0, area), r+25)
        if event and r >= event[2]:
            event = None
        # --- Phase de setup (élection CH style LEACH) ---
        period = round(1/p)
        chs = []
        for i in alive:
            if r - last_ch[i] >= period:
                thr = p / (1 - p*(r % period))
                if rnd.random() < thr:
                    chs.append(i)
        if not chs:
            chs = [rnd.choice(alive)]
        for i in chs:
            last_ch[i] = r
        # advertisement (+ HT, ST, attributs) en broadcast
        adv_d = D0  # portée de broadcast limitée à d0 (sinon coût multipath énorme)
        for c in chs:
            energy[c] -= etx(CTRL, adv_d)
        for i in alive:
            if i not in chs:
                energy[i] -= erx(CTRL)*len(chs)
        members = {c: [] for c in chs}
        for i in alive:
            if i in chs: continue
            c = min(chs, key=lambda c: dist(pos[i], pos[c]))
            members[c].append(i)
            energy[i] -= etx(CTRL, dist(pos[i], pos[c]))   # join
            energy[c] -= erx(CTRL)
        for c in chs:
            energy[c] -= etx(CTRL, 30)                      # schedule
        setup_msgs = len(chs) + (len(alive)-len(chs)) + len(chs)
        ctrl_msgs_setup.append(setup_msgs)
        # --- Phase de transmission réactive (TEEN) ---
        for c in chs:
            for i in members[c]:
                if energy[i] <= 0: continue
                v = 22 + rnd.gauss(0, 0.5)
                if event and dist(pos[i], event[:2]) < 50:
                    v = 36 + rnd.gauss(0, 1.0)
                transmit = v >= ht and (sv[i] is None or abs(v - sv[i]) >= st)
                if transmit:
                    sv[i] = v
                    sent += 1
                    energy[i] -= etx(PKT, dist(pos[i], pos[c]))
                    if energy[c] > 0:
                        energy[c] -= erx(PKT)
                        if rnd.random() > per:           # lien capteur->CH
                            energy[c] -= etx(PKT, dist(pos[c], bs))
                            if rnd.random() > per:       # lien CH->BS
                                recv += 1
        energy = [max(e, 0.0) for e in energy]
        if first_dead is None and min(energy) == 0:
            first_dead = r
        rows.append((r, sum(energy), sent, recv, setup_msgs))
    pdr = recv/sent if sent else float('nan')
    avg_setup = sum(ctrl_msgs_setup)/len(ctrl_msgs_setup)
    if out:
        with open(out, 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['round','residual_energy','sent','received','setup_msgs']); w.writerows(rows)
    return dict(nodes=n, pdr=round(pdr,3), sent=sent, recv=recv, first_dead=first_dead,
                final_energy=round(rows[-1][1],3), avg_setup_msgs=round(avg_setup,1))

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--nodes', type=int, default=100)
    ap.add_argument('--rounds', type=int, default=1000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    print(run(a.nodes, a.rounds, a.seed, out=a.out))
