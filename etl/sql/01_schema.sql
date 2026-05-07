CREATE SCHEMA IF NOT EXISTS ter;

CREATE TABLE IF NOT EXISTS ter.ref_operator (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS ter.admin_boundary (
    id BIGSERIAL PRIMARY KEY,
    level TEXT NOT NULL,
    code TEXT,
    name TEXT NOT NULL,
    geom geometry(MultiPolygon, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS ter.radio_site (
    id BIGSERIAL PRIMARY KEY,
    site_id TEXT,
    operator_id INT REFERENCES ter.ref_operator(id),
    tech TEXT NOT NULL CHECK (tech IN ('4G', '5G')),
    band TEXT,
    source_name TEXT,
    geom geometry(Point, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS ter.road_segment (
    id BIGSERIAL PRIMARY KEY,
    source_id TEXT,
    road_name TEXT,
    road_type TEXT NOT NULL,
    length_m DOUBLE PRECISION,
    region_code TEXT,
    dept_code TEXT,
    geom geometry(LineString, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS ter.road_sample_point (
    id BIGSERIAL PRIMARY KEY,
    segment_id BIGINT REFERENCES ter.road_segment(id) ON DELETE CASCADE,
    seq_idx INT NOT NULL,
    measure_m DOUBLE PRECISION NOT NULL,
    geom geometry(Point, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS ter.coverage_official (
    id BIGSERIAL PRIMARY KEY,
    operator_id INT REFERENCES ter.ref_operator(id),
    tech TEXT CHECK (tech IN ('4G', '5G')),
    quality_class TEXT,
    source_name TEXT,
    geom geometry(MultiPolygon, 4326) NOT NULL
);

CREATE TABLE IF NOT EXISTS ter.sample_coverage (
    id BIGSERIAL PRIMARY KEY,
    sample_point_id BIGINT REFERENCES ter.road_sample_point(id) ON DELETE CASCADE,
    method TEXT NOT NULL CHECK (method IN ('A_THEORETICAL', 'B_OFFICIAL')),
    tech TEXT NOT NULL CHECK (tech IN ('4G', '5G')),
    operator_id INT REFERENCES ter.ref_operator(id),
    is_covered BOOLEAN NOT NULL,
    nearest_site_id BIGINT REFERENCES ter.radio_site(id),
    distance_to_site_m DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT NOW()
);
