from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..db.session import get_db
from ..services.geojson_service import fetch_geojson
from ..schemas.filters import GeoFilter

router = APIRouter(prefix="/api/v1/roads", tags=["roads"])


def fetch_sample_points_geojson(db: Session, limit: int, bbox: tuple | None, region_code: str | None, dept_code: str | None):
    conditions: list[str] = []
    params: dict = {"limit": limit}

    if bbox:
        conditions.append("ST_Intersects(rsp.geom, ST_MakeEnvelope(:minx, :miny, :maxx, :maxy, 4326))")
        params.update({"minx": bbox[0], "miny": bbox[1], "maxx": bbox[2], "maxy": bbox[3]})

    if region_code:
        conditions.append("rs.region_code = :region_code")
        params["region_code"] = region_code

    if dept_code:
        conditions.append("rs.dept_code = :dept_code")
        params["dept_code"] = dept_code

    where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = text(
        f"""
        SELECT json_build_object(
          'type', 'FeatureCollection',
          'features', COALESCE(json_agg(feature), '[]'::json)
        )
        FROM (
          SELECT json_build_object(
            'type', 'Feature',
            'id', rsp.id,
            'geometry', ST_AsGeoJSON(rsp.geom)::json,
            'properties', to_jsonb(rsp) - 'geom'
          ) AS feature
          FROM ter.road_sample_point rsp
          JOIN ter.road_segment rs ON rs.id = rsp.segment_id
          {where_sql}
          LIMIT :limit
        ) f;
        """
    )
    return db.execute(query, params).scalar_one()


@router.get("/segments")
def get_segments(
    bbox: str | None = Query(default=None),
    road_type: str | None = Query(default=None),
    region_code: str | None = Query(default=None),
    dept_code: str | None = Query(default=None),
    limit: int = Query(default=5000, ge=1, le=50000),
    db: Session = Depends(get_db),
):
    gf = GeoFilter(bbox=bbox, road_type=road_type, region_code=region_code, dept_code=dept_code, limit=limit)
    try:
        bb = gf.bbox_tuple()
        return fetch_geojson(
            db,
            "ter.road_segment",
            gf.limit,
            {
                "bbox": bb,
                "road_type": gf.road_type,
                "region_code": gf.region_code,
                "dept_code": gf.dept_code,
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sample-points")
def get_sample_points(
    bbox: str | None = Query(default=None),
    region_code: str | None = Query(default=None),
    dept_code: str | None = Query(default=None),
    limit: int = Query(default=10000, ge=1, le=50000),
    db: Session = Depends(get_db),
):
    gf = GeoFilter(bbox=bbox, region_code=region_code, dept_code=dept_code, limit=limit)
    try:
        bb = gf.bbox_tuple()
        return fetch_sample_points_geojson(db, gf.limit, bb, gf.region_code, gf.dept_code)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
