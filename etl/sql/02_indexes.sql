CREATE INDEX IF NOT EXISTS idx_admin_boundary_geom ON ter.admin_boundary USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_radio_site_geom ON ter.radio_site USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_road_segment_geom ON ter.road_segment USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_road_sample_point_geom ON ter.road_sample_point USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_coverage_official_geom ON ter.coverage_official USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_sample_cov_lookup ON ter.sample_coverage(method, tech, operator_id, is_covered);
