import argparse, csv, matplotlib, os
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from teen_ref import run

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')


def plot_reference():
    for n in (50, 100, 300):
        print(run(n, 1000, 1,
                  out=os.path.join(RESULTS_DIR, 'ref_teen_%d.csv' % n)))
    x, y = [], []
    with open(os.path.join(RESULTS_DIR, 'ref_teen_100.csv')) as source:
        for row in csv.DictReader(source):
            x.append(int(row['round']))
            y.append(float(row['residual_energy']))
    plt.plot(x, y)
    plt.xlabel('Round')
    plt.ylabel('Énergie résiduelle totale (J)')
    plt.title('TEEN (référence Python) - 100 noeuds')
    plt.grid(True)
    plt.savefig(os.path.join(RESULTS_DIR, 'energie_teen_ref.png'), dpi=150)


def plot_tossim():
    missing = [
        os.path.join(RESULTS_DIR, 'tossim_teen_%d.csv' % nodes)
        for nodes in (50, 100, 300)
        if not os.path.exists(
            os.path.join(RESULTS_DIR, 'tossim_teen_%d.csv' % nodes))
    ]
    if missing:
        missing_files = ', '.join(os.path.basename(path) for path in missing)
        raise IOError(
            'Résultats TOSSIM manquants : %s. Depuis la racine du projet, '
            'lancez : docker compose -f docker/docker-compose.yml run --rm '
            'tossim python2 /work/tossim/run_sim.py --all-sizes'
            % missing_files)

    figure, axes = plt.subplots(3, 1, figsize=(9, 11), sharex=True)
    for nodes in (50, 100, 300):
        path = os.path.join(RESULTS_DIR, 'tossim_teen_%d.csv' % nodes)
        rounds, energy, setup, cumulative_pdr = [], [], [], []
        sent_total = received_total = 0
        with open(path) as source:
            for row in csv.DictReader(source):
                rounds.append(int(row['round']))
                energy.append(float(row['residual_energy']))
                setup.append(int(row['setup_msgs']))
                sent_total += int(row['sent'])
                received_total += int(row['received'])
                cumulative_pdr.append(
                    float(received_total) / sent_total if sent_total else 0.0)
        label = '%d noeuds' % nodes
        axes[0].plot(rounds, energy, label=label)
        axes[1].plot(rounds, setup, label=label)
        axes[2].plot(rounds, cumulative_pdr, label=label)

    axes[0].set_ylabel('Énergie résiduelle (J)')
    axes[1].set_ylabel('Messages setup / round')
    axes[2].set_ylabel('PDR cumulatif')
    axes[2].set_xlabel('Round')
    for axis in axes:
        axis.grid(True)
        axis.legend()
    figure.suptitle('TEEN sur TOSSIM')
    figure.tight_layout()
    figure.savefig(os.path.join(RESULTS_DIR, 'energie_teen_tossim.png'), dpi=150)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--tossim', action='store_true',
                        help='tracer les CSV générés par tossim/run_sim.py')
    args = parser.parse_args()
    if args.tossim:
        plot_tossim()
    else:
        plot_reference()
