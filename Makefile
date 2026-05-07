.PHONY: up down logs db-init demo-etl demo-check test-backend test-etl

DEMO_BBOX ?= 3.20,44.40,3.80,44.90
DATABASE_URL ?= postgresql+psycopg://postgres:postgres@localhost:5432/ter
API_BASE ?= http://localhost:8005

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=100

db-init:
	docker compose exec -T db psql -U postgres -d ter < etl/sql/00_extensions.sql
	docker compose exec -T db psql -U postgres -d ter < etl/sql/01_schema.sql
	docker compose exec -T db psql -U postgres -d ter < etl/sql/02_indexes.sql

demo-etl:
	cd etl && DATABASE_URL='$(DATABASE_URL)' python scripts/load_coverage.py --input ../data/processed/coverage/orange/arcep_couverture_orange_4g.gpkg/2025_T4_couv_Metropole_OF_4G_data.gpkg --bbox $(DEMO_BBOX)
	cd etl && DATABASE_URL='$(DATABASE_URL)' python scripts/load_coverage.py --input ../data/processed/coverage/bouygues/arcep_couverture_bouygues_4g.gpkg/2025_T4_couv_Metropole_BOUY_4G_data.gpkg --bbox $(DEMO_BBOX) --append
	cd etl && DATABASE_URL='$(DATABASE_URL)' python scripts/load_coverage.py --input ../data/processed/coverage/free/arcep_couverture_free_4g.gpkg/2025_T4_couv_Metropole_FREE_4G_data.gpkg --bbox $(DEMO_BBOX) --append
	cd etl && DATABASE_URL='$(DATABASE_URL)' python scripts/load_coverage.py --input ../data/processed/coverage/sfr/arcep_couverture_sfr_4g.gpkg/2025_T4_couv_Metropole_SFR0_4G_data.gpkg --bbox $(DEMO_BBOX) --append
	cd etl && DATABASE_URL='$(DATABASE_URL)' python scripts/sample_points.py --bbox $(DEMO_BBOX)
	cd etl && DATABASE_URL='$(DATABASE_URL)' python scripts/compute_coverage_a.py --bbox $(DEMO_BBOX)
	cd etl && DATABASE_URL='$(DATABASE_URL)' python scripts/compute_coverage_b.py --bbox $(DEMO_BBOX)

demo-check:
	docker compose exec -T db psql -U postgres -d ter -c "SELECT COUNT(*) AS routes FROM ter.road_segment;"
	docker compose exec -T db psql -U postgres -d ter -c "SELECT COUNT(*) AS sites FROM ter.radio_site;"
	docker compose exec -T db psql -U postgres -d ter -c "SELECT COUNT(*) AS sample_points FROM ter.road_sample_point;"
	docker compose exec -T db psql -U postgres -d ter -c "SELECT o.name, c.tech, COUNT(*) FROM ter.coverage_official c JOIN ter.ref_operator o ON o.id = c.operator_id GROUP BY o.name, c.tech ORDER BY o.name, c.tech;"
	docker compose exec -T db psql -U postgres -d ter -c "SELECT method, tech, is_covered, COUNT(*) FROM ter.sample_coverage GROUP BY method, tech, is_covered ORDER BY method, tech, is_covered;"
	curl -sS '$(API_BASE)/api/v1/stats/compare?tech=4G'

test-backend:
	cd backend && python -m py_compile app/main.py app/api/routes.py app/api/coverage.py app/api/stats.py app/db/session.py app/services/geojson_service.py

test-etl:
	cd etl && python -m py_compile scripts/config.py scripts/db.py scripts/filters.py scripts/postgis_io.py scripts/load_admin.py scripts/load_roads.py scripts/load_sites.py scripts/load_coverage.py scripts/prepare_roads.py scripts/run_pipeline.py scripts/sample_points.py scripts/compute_coverage_a.py scripts/compute_coverage_b.py
