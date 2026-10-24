# TP Réseaux sans fil — TEEN sur TOSSIM

Scénario : 100 nœuds aléatoires sur 200x200 m, BS en (100,250), E0 = 0.5 J, 1000 rounds,
modèle radio 1er ordre (Eelec=50 nJ/bit, εfs=10 pJ/bit/m², εmp=0.0013 nJ/bit/m⁴, d0≈87.7 m).

## Arborescence
- `docker/` : environnement TinyOS/TOSSIM (Dockerfile + compose)
- `scripts/gen_topology.py` : topologies 50/100/300 nœuds (nœud 0 = BS)
- `python_ref/` : simulation de référence TEEN (Python 3) → valeurs attendues + modèle d'énergie
- `tossim/` : application nesC TEEN + script Python TOSSIM (à venir)
- `results/` : CSV et courbes
- `report/` : rapport (4 pages max)

## Utilisation
    cd python_ref && python3 plot.py        # courbes de référence
    python3 ../scripts/gen_topology.py 100 1 > ../tossim/topology_100.txt
    cd docker && docker compose run --rm tossim

## Points d'attention (à justifier dans le rapport)
- TOSSIM n'a pas de modèle d'énergie natif : l'énergie est comptabilisée au niveau applicatif
  (formules du modèle radio de premier ordre appliquées aux paquets envoyés/reçus).
- Taille des paquets (`PKT`) : 4000 bits avec BS à 250 m rend l'énergie de 0.5 J insuffisante (voir ci-dessous).
- Le délai de setup se mesure en messages de contrôle (annonce + join + schedule) par round.
