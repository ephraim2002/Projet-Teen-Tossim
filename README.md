# TP Réseaux sans fil — TEEN sur TOSSIM

Ce dépôt contient une implémentation de l'algorithme TEEN en nesC, exécutée
dans le simulateur réseau TOSSIM de TinyOS, ainsi qu'une simulation Python de
référence.

## Scénario demandé

Le scénario principal utilise 100 capteurs tirés aléatoirement dans une zone
de 200 x 200 m, une station de base (BS) située en (100, 250), une énergie
initiale de 0,5 J par capteur et 1 000 rounds. Les scénarios de comparaison
utilisent 50, 100 et 300 capteurs. Le numéro de nœud 0 est réservé à la BS ;
ainsi, une simulation de 100 capteurs configure 101 nœuds TOSSIM au total.

Le modèle énergétique radio de premier ordre utilise les coefficients indiqués
dans le sujet : Eelec = 50 nJ/bit, εfs = 10 pJ/bit/m² et
εmp = 0,0013 nJ/bit/m⁴. En appliquant ces unités, la distance de transition est
d0 = sqrt(εfs / εmp) ≈ 2,77 m.

## Organisation du projet

- `tossim/teen/TeenC.nc` : logique TEEN exécutée par chaque nœud (élection des
  chefs de cluster, annonces, adhésion, seuils et acheminement des données).
- `tossim/teen/TeenAppC.nc` : configuration TinyOS qui relie l'application aux
  timers, à la radio et aux composants TOSSIM.
- `tossim/teen/Makefile` : compilation de l'application et des bindings TOSSIM.
- `tossim/run_sim.py` : génération de la topologie, compilation, exécution de
  la simulation et export des métriques.
- `scripts/gen_topology.py` : génération autonome d'une topologie aléatoire.
- `python_ref/` : simulation Python de référence et génération des graphiques.
- `results/` : résultats Python existants et résultats produits par TOSSIM.
- `docker/` : image Docker TinyOS/TOSSIM et configuration Docker Compose.

## Prérequis

1. Installer et démarrer Docker Desktop (Windows) ou Docker Engine (Linux).
2. Ouvrir un terminal **à la racine du dépôt**, c'est-à-dire dans le dossier
   qui contient `README.md` et le dossier `docker`.
3. Vérifier que Docker répond :

   ```powershell
   docker --version
   docker compose version
   ```

TinyOS/TOSSIM et nesC sont installés dans l'image Docker. Il n'est donc pas
nécessaire d'installer Python 2 ou TinyOS sur l'ordinateur hôte pour exécuter
la simulation TOSSIM.

## Exécuter les simulations TOSSIM

Les commandes ci-dessous sont à lancer depuis la racine du projet. Elles sont
écrites sur une seule ligne pour être copiées directement dans PowerShell.

### 1. Construire l'image Docker

À effectuer la première fois, ou après une modification de `docker/Dockerfile` :

```powershell
docker compose -f docker/docker-compose.yml build tossim
```

### 2. Lancer les trois tailles demandées

Cette commande exécute successivement les scénarios de **50, 100 et
300 capteurs**, avec 1 000 rounds et la graine aléatoire 1 :

```powershell
docker compose -f docker/docker-compose.yml run --rm tossim python2 /work/tossim/run_sim.py --all-sizes
```

L'option `--all-sizes` demande au script de lancer les trois tailles. La
commande doit se terminer par cette option : ne pas laisser un `--` isolé à la
fin de la ligne.

### 3. Lancer seulement le scénario principal

```powershell
docker compose -f docker/docker-compose.yml run --rm tossim python2 /work/tossim/run_sim.py --nodes 100 --rounds 1000 --seed 1
```

Les options signifient :

- `--nodes 100` : nombre de capteurs, sans compter la BS ;
- `--rounds 1000` : nombre de rounds simulés ;
- `--seed 1` : graine du générateur aléatoire, pour pouvoir reproduire la même
  topologie.

### 4. Lancer un essai court

Avant une simulation longue, on peut tester la compilation et la génération des
résultats avec 10 rounds :

```powershell
docker compose -f docker/docker-compose.yml run --rm tossim python2 /work/tossim/run_sim.py --nodes 50 --rounds 10 --seed 1
```

### Paramètres disponibles

Le script accepte les paramètres suivants :

| Paramètre | Valeur par défaut | Description |
|---|---:|---|
| `--nodes N` | `100` | Nombre de capteurs à déployer |
| `--rounds R` | `1000` | Nombre de rounds |
| `--seed S` | `1` | Graine de génération de la topologie |
| `--all-sizes` | désactivé | Lance successivement 50, 100 et 300 capteurs |

Par exemple, pour lancer 300 capteurs pendant 200 rounds avec une autre
topologie :

```powershell
docker compose -f docker/docker-compose.yml run --rm tossim python2 /work/tossim/run_sim.py --nodes 300 --rounds 200 --seed 42
```

Si l'image n'a pas encore été construite, exécuter d'abord l'étape de
construction ci-dessus ou ajouter `--build` après `run`. Pour forcer sa
reconstruction :

```powershell
docker compose -f docker/docker-compose.yml run --build --rm tossim python2 /work/tossim/run_sim.py --nodes 100 --rounds 1000 --seed 1
```

L'option `--rm` supprime le conteneur temporaire à la fin. Les résultats restent
dans `results/`, car le dépôt est monté dans le conteneur par Docker Compose.

## Fichiers produits et métriques

Les fichiers sont écrits dans le dossier `results/` du dépôt, partagé avec le
conteneur Docker :

- `tossim_teen_50.csv`, `tossim_teen_100.csv` et `tossim_teen_300.csv` :
  mesures round par round ;
- `tossim_teen_<n>.log` : journal brut des événements TEEN pour une simulation
  de `n` capteurs ;
- `tossim/topology_<n>.txt` : coordonnées générées pour les n capteurs et la
  BS ;
- `tossim/teen/Topology.h` : coordonnées et paramètres transmis à l'application
  nesC pour la compilation.

Chaque CSV contient les colonnes suivantes :

| Colonne | Signification |
|---|---|
| `round` | Numéro du round |
| `residual_energy` | Énergie résiduelle totale des capteurs, en joules |
| `sent` | Paquets de données émis par les capteurs pendant ce round |
| `received` | Données reçues par la BS pendant ce round |
| `setup_msgs` | Messages de contrôle d'annonce, d'adhésion et de schedule |

Le PDR (Packet Delivery Ratio) affiché à la fin est calculé comme le nombre de
données reçues à la BS divisé par le nombre de données émises. Les paquets de
contrôle ne sont pas comptés dans ce ratio. Le temps d'exécution affiché est le
temps réel nécessaire au simulateur pour terminer, et non le délai de
convergence radio.

## Générer les graphiques

Après avoir terminé les simulations 50, 100 et 300 capteurs, installer les
dépendances Python 3 sur l'ordinateur hôte (à faire une seule fois) :

```powershell
python -m pip install -r python_ref/requirements.txt
```

Puis générer les graphiques des résultats TOSSIM :

```powershell
python python_ref/plot.py --tossim
```

Le graphique comparatif est enregistré sous
`results/energie_teen_tossim.png`. Il présente l'énergie résiduelle, les
messages de setup par round et le PDR cumulatif. Les trois CSV TOSSIM doivent
être présents ; sinon, le script indique quel résultat manque.

Pour générer les résultats et le graphique de la simulation Python de
référence, exécuter plutôt :

```powershell
python -m pip install -r python_ref/requirements.txt
python python_ref/plot.py
```

Ces résultats de référence ne sont pas des mesures TOSSIM : ils proviennent
d'un modèle Python distinct et doivent être comparés en tenant compte de leurs
hypothèses respectives.

## Hypothèses et limites du modèle

- TOSSIM ne modélise pas directement la batterie du sujet. L'application
  comptabilise l'énergie de transmission et de réception au niveau nesC avec
  le modèle radio de premier ordre et les distances de la topologie.
- La topologie radio est construite à partir de la distance entre chaque paire
  de nœuds. Le modèle TOSSIM prend en charge les transmissions et collisions ;
  l'application ajoute aussi une probabilité de perte de 2 % aux messages
  unicast.
- Les capteurs échantillonnent une valeur par round. Le phénomène est simulé
  dans une zone de 100 m autour de la BS, active pendant 25 rounds sur 100.
  Les seuils TEEN utilisés sont HT = 30 et ST = 2.
- Le calcul énergétique considère 4 000 bits pour un paquet de données et
  200 bits pour un message de contrôle. Les données reçues par un chef de
  cluster sont agrégées avant le transfert vers la BS.
- Pour mesurer le passage à l'échelle, le script rapporte le nombre de
  messages de setup par round. Le temps réel est également affiché à titre
  indicatif.
