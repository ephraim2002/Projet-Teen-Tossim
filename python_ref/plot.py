import csv, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from teen_ref import run

for n in (50, 100, 300):
    print(run(n, 1000, 1, out=f'../results/ref_teen_{n}.csv'))
x, y = [], []
for row in csv.DictReader(open('../results/ref_teen_100.csv')):
    x.append(int(row['round'])); y.append(float(row['residual_energy']))
plt.plot(x, y); plt.xlabel('Round'); plt.ylabel('Énergie résiduelle totale (J)')
plt.title('TEEN (référence Python) - 100 noeuds'); plt.grid(True)
plt.savefig('../results/energie_teen_ref.png', dpi=150)
