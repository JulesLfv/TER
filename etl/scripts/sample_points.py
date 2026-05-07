import argparse
from sqlalchemy import create_engine, text
from config import settings
from filters import bbox_params, bbox_sql, parse_bbox


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bbox", default=None, help="Optional EPSG:4326 bbox: minx,miny,maxx,maxy")
    parser.add_argument("--append", action="store_true", help="Append instead of replacing road_sample_point")
    args = parser.parse_args()
    bbox = parse_bbox(args.bbox)
    where_sql = f"WHERE {bbox_sql('s.geom')}" if bbox else ""

    engine = create_engine(settings.database_url)
    sql = text(
        f"""
        INSERT INTO ter.road_sample_point (segment_id, seq_idx, measure_m, geom)
        SELECT s.id,
               gs.idx,
               gs.idx * :step AS measure_m,
               ST_Transform(
                 ST_LineInterpolatePoint(ST_Transform(s.geom, 2154),
                 LEAST((gs.idx * :step) / NULLIF(ST_Length(ST_Transform(s.geom,2154)),0),1)),
               4326) AS geom
        FROM ter.road_segment s
        JOIN LATERAL (
          SELECT generate_series(0, floor(ST_Length(ST_Transform(s.geom, 2154))/:step)::int) AS idx
        ) gs ON TRUE
        {where_sql}
        ;
        """
    )
    with engine.begin() as conn:
        if not args.append:
            conn.execute(text("TRUNCATE ter.road_sample_point RESTART IDENTITY CASCADE"))
        conn.execute(sql, {"step": settings.sample_step_m, **bbox_params(bbox)})


if __name__ == "__main__":
    main()
