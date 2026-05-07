from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..services.geojson_service import fetch_geojson
from ..schemas.filters import GeoFilter

router = APIRouter(prefix="/api/v1", tags=["coverage"])


@router.get("/operators")
def get_operators(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, name FROM ter.ref_operator ORDER BY name")).mappings().all()
    return {"items": [dict(row) for row in rows]}


@router.get("/radio-sites")
def get_radio_sites(
    bbox: str | None = Query(default=None),
    tech: str | None = Query(default=None),
    operator_id: int | None = Query(default=None),
    limit: int = Query(default=10000, ge=1, le=50000),
    db: Session = Depends(get_db),
):
    gf = GeoFilter(bbox=bbox, tech=tech, operator_id=operator_id, limit=limit)
    try:
        bb = gf.bbox_tuple()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    conditions = [
        "(CAST(:tech AS text) IS NULL OR rs.tech = CAST(:tech AS text))",
        "(CAST(:operator_id AS integer) IS NULL OR rs.operator_id = CAST(:operator_id AS integer))",
    ]
    params = {"tech": gf.tech, "operator_id": gf.operator_id, "limit": gf.limit}
    if bb:
        conditions.append("ST_Intersects(rs.geom, ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326))")
        params.update({"minx": bb[0], "miny": bb[1], "maxx": bb[2], "maxy": bb[3]})

    query = text(
        f"""
        SELECT json_build_object(
          'type', 'FeatureCollection',
          'features', COALESCE(json_agg(feature), '[]'::json)
        )
        FROM (
          SELECT json_build_object(
            'type', 'Feature',
            'id', rs.id,
            'geometry', ST_AsGeoJSON(rs.geom)::json,
            'properties', json_build_object(
                'site_id', rs.site_id,
                'operator_id', rs.operator_id,
                'operator_name', op.name,
                'tech', rs.tech,
                'band', rs.band,
                'source_name', rs.source_name
            )
          ) AS feature
          FROM ter.radio_site rs
          LEFT JOIN ter.ref_operator op ON op.id = rs.operator_id
          WHERE {' AND '.join(conditions)}
          LIMIT :limit
        ) f;
        """
    )
    return db.execute(query, params).scalar_one()


@router.get("/coverage/official")
def get_official_coverage(
    bbox: str | None = Query(default=None),
    tech: str | None = Query(default=None),
    operator_id: int | None = Query(default=None),
    limit: int = Query(default=5000, ge=1, le=50000),
    db: Session = Depends(get_db),
):
    gf = GeoFilter(bbox=bbox, tech=tech, operator_id=operator_id, limit=limit)
    try:
        bb = gf.bbox_tuple()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return fetch_geojson(db, "ter.coverage_official", gf.limit, {"bbox": bb, "tech": gf.tech, "operator_id": gf.operator_id})


@router.get("/coverage/sample-points")
def get_coverage_sample_points(
    bbox: str | None = Query(default=None),
    tech: str | None = Query(default=None),
    operator_id: int | None = Query(default=None),
    method: str | None = Query(default="B_OFFICIAL"),
    limit: int = Query(default=20000, ge=1, le=100000),
    db: Session = Depends(get_db),
):
    gf = GeoFilter(bbox=bbox, tech=tech, operator_id=operator_id, method=method, limit=limit)
    try:
        bb = gf.bbox_tuple()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    conditions = [
        "(CAST(:tech AS text) IS NULL OR sc.tech = CAST(:tech AS text))",
        "(CAST(:method AS text) IS NULL OR sc.method = CAST(:method AS text))",
        "(CAST(:operator_id AS integer) IS NULL OR sc.operator_id = CAST(:operator_id AS integer))",
    ]
    params = {"tech": gf.tech, "method": gf.method, "operator_id": gf.operator_id, "limit": gf.limit}

    if bb:
        conditions.append("ST_Intersects(p.geom, ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326))")
        params.update({"minx": bb[0], "miny": bb[1], "maxx": bb[2], "maxy": bb[3]})

    query = text(
        f"""
        SELECT json_build_object(
          'type', 'FeatureCollection',
          'features', COALESCE(json_agg(feature), '[]'::json)
        )
        FROM (
          SELECT json_build_object(
            'type', 'Feature',
            'id', sc.id,
            'geometry', ST_AsGeoJSON(p.geom)::json,
            'properties', json_build_object(
                'sample_point_id', p.id,
                'segment_id', p.segment_id,
                'method', sc.method,
                'tech', sc.tech,
                'operator_id', sc.operator_id,
                'is_covered', sc.is_covered,
                'distance_to_site_m', sc.distance_to_site_m
            )
          ) AS feature
          FROM ter.sample_coverage sc
          JOIN ter.road_sample_point p ON p.id = sc.sample_point_id
          WHERE {' AND '.join(conditions)}
          LIMIT :limit
        ) f;
        """
    )
    return db.execute(query, params).scalar_one()
