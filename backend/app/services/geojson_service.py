from sqlalchemy import text

ALLOWED_TABLES = {
    "ter.road_segment": {"id", "geom", "road_type", "region_code", "dept_code"},
    "ter.road_sample_point": {"id", "geom"},
    "ter.radio_site": {"id", "geom", "tech", "operator_id"},
    "ter.coverage_official": {"id", "geom", "tech", "operator_id"},
}


def _build_where(conditions: list[str]) -> str:
    return f"WHERE {' AND '.join(conditions)}" if conditions else ""


def fetch_geojson(db, table: str, limit: int = 5000, filters: dict | None = None):
    if table not in ALLOWED_TABLES:
        raise ValueError(f"Table not allowed: {table}")

    if filters is None:
        filters = {}

    conditions: list[str] = []
    params: dict = {"limit": limit}

    bbox = filters.get("bbox")
    if bbox:
        conditions.append("ST_Intersects(geom, ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326))")
        params.update({"minx": bbox[0], "miny": bbox[1], "maxx": bbox[2], "maxy": bbox[3]})

    for key in ("tech", "operator_id", "road_type", "region_code", "dept_code", "method"):
        if filters.get(key) is not None:
            if key not in ALLOWED_TABLES[table]:
                continue
            conditions.append(f"{key} = :{key}")
            params[key] = filters[key]

    where_sql = _build_where(conditions)
    query = text(
        f"""
        SELECT json_build_object(
          'type', 'FeatureCollection',
          'features', COALESCE(json_agg(feature), '[]'::json)
        )
        FROM (
          SELECT json_build_object(
            'type', 'Feature',
            'id', id,
            'geometry', ST_AsGeoJSON(geom)::json,
            'properties', to_jsonb(t) - 'geom'
          ) AS feature
          FROM {table} t
          {where_sql}
          LIMIT :limit
        ) f;
        """
    )
    return db.execute(query, params).scalar_one()
