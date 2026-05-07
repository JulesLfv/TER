# TER — Analyse de la couverture 4G/5G des routes en France

Application web SIG pour analyser la couverture mobile 4G/5G le long du réseau routier français.

Le projet distingue deux méthodes:

- **A_THEORETICAL**: approximation pédagogique par distance au site radio compatible le plus proche.
- **B_OFFICIAL**: couverture issue d'une couche officielle ARCEP.

## État Actuel

On dispose d'une démo MVP validée sur une zone pilote en Lozère:

```text
bbox = 3.20,44.40,3.80,44.90
```

La démo affiche:

- routes OSM filtrées;
- antennes ARCEP 4G/5G, filtrables et cliquables;
- points routiers couverts/non couverts selon `B_OFFICIAL`;
- KPI en kilomètres;
- comparaison A/B par opérateur.

## Structure

```text
TER/
├── backend/        # FastAPI + accès PostGIS
├── etl/            # SQL et scripts géospatiaux
├── frontend/       # React + Vite + Leaflet
├── data/           # raw / processed / exports
├── dl_data.py      # téléchargement des sources publiques
├── docker-compose.yml
├── Makefile
└── TODO.md
```

## Lancement Docker

```bash
make up
make db-init
```

Services exposés:

- Frontend: http://localhost:5173
- API: http://localhost:8005
- API docs: http://localhost:8005/docs
- PostGIS: `localhost:5432` par défaut dans `docker-compose.yml`

Vérification rapide:

```bash
curl http://localhost:8005/health
```

## Sources De Données

Télécharger les sources publiques:

```bash
python dl_data.py --dry-run
python dl_data.py --skip-existing --extract
```

Le downloader récupère:

- routes OSM France via Geofabrik: `france-latest.osm.pbf`;
- sites radio ARCEP Métropole: dernier CSV `sites_Metropole`;
- couvertures ARCEP 4G/5G Métropole pour Bouygues, Free, Orange et SFR;
- limites départementales GeoJSON.

Les couvertures ARCEP sont des archives `.gpkg.7z`; l'option `--extract` nécessite `7z`/`7za`.

## Préparation Initiale

Installer les dépendances ETL:

```bash
cd etl
pip install -r requirements.txt
export DATABASE_URL='postgresql+psycopg://postgres:postgres@localhost:5432/ter'
cd ..
```

Préparer les routes OSM:

```bash
python etl/scripts/prepare_roads.py \
  --input data/raw/roads/france-latest.osm.pbf \
  --output data/processed/roads.geojson
```

Charger les tables de base une première fois:

```bash
cd etl
python scripts/load_admin.py --input ../data/raw/admin/departements.geojson --level department
python scripts/load_roads.py --input ../data/processed/roads.geojson --type-col highway --source-id-col osm_id
python scripts/load_sites.py --input ../data/raw/sites/arcep_sites_2g_3g_4g_5g.csv --format arcep-csv
cd ..
```

## Démo Lozère

Une fois les routes/sites/admin chargés, relancer la démo validée:

```bash
make demo-etl
```

Cette commande:

- charge les couvertures ARCEP 4G des 4 opérateurs sur la bbox Lozère;
- recrée les points routiers échantillonnés sur la bbox;
- recalcule `A_THEORETICAL`;
- recalcule `B_OFFICIAL`.

Contrôler l'état:

```bash
make demo-check
```

Puis ouvrir:

```text
http://localhost:5173
```

## Interface

Le panneau de gauche permet de:

- choisir la technologie utilisée pour les stats/couverture;
- choisir l'opérateur par nom;
- filtrer l'affichage des antennes: `4G + 5G`, `4G seulement`, `5G seulement`;
- activer/désactiver les routes;
- activer/désactiver les antennes;
- activer/désactiver les points couverts/non couverts.

Sur la carte:

- routes = bleu;
- antennes 4G = rouge;
- antennes 5G = violet;
- points verts = route couverte selon `B_OFFICIAL`;
- points rouges = route non couverte selon `B_OFFICIAL`.

Cliquer sur une antenne affiche son opérateur, sa technologie, son identifiant de site et sa bande si disponible.

## API Principale

- `GET /health`
- `GET /api/v1/operators`
- `GET /api/v1/roads/segments`
- `GET /api/v1/roads/sample-points`
- `GET /api/v1/radio-sites`
- `GET /api/v1/coverage/official`
- `GET /api/v1/coverage/sample-points`
- `GET /api/v1/stats/summary`
- `GET /api/v1/stats/compare`

Exemples:

```bash
curl 'http://localhost:8005/api/v1/stats/summary?tech=4G'
curl 'http://localhost:8005/api/v1/stats/compare?tech=4G'
curl 'http://localhost:8005/api/v1/coverage/sample-points?tech=4G&operator_id=3&method=B_OFFICIAL'
```

## Méthodologie

Les données API et web sont en EPSG:4326. Les calculs métriques utilisent EPSG:2154 lorsque nécessaire.

Le niveau d'analyse est le point routier échantillonné, rattaché à un tronçon. Les statistiques en kilomètres approximent la longueur représentée par chaque point pour produire des ratios lisibles.

Limites importantes:

- `A_THEORETICAL` est une approximation par distance; elle ne modélise ni relief, ni orientation d'antenne, ni charge réseau.
- `B_OFFICIAL` dépend de la couverture ARCEP chargée dans la zone pilote.
- La démo validée ne traite pas la France entière; les traitements nationaux doivent être faits par lots département/région.
- Les filtres `region_code` et `dept_code` existent côté API, mais les routes chargées actuellement ont encore ces champs à `NULL`.
- Les gros GPKG ARCEP France entière peuvent saturer la RAM; utiliser `--bbox` pour charger une zone pilote.

## Validation Développement

```bash
python -m compileall backend etl
cd frontend && npm run build
```

Commandes utiles:

```bash
make test-backend
make test-etl
make demo-check
```
