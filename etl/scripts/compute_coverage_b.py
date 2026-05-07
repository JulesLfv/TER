import argparse
from sqlalchemy import create_engine, text
from config import settings
from filters import bbox_params, bbox_sql, parse_bbox


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bbox", default=None, help="Optional EPSG:4326 bbox: minx,miny,maxx,maxy")
    parser.add_argument("--append", action="store_true", help="Append instead of replacing B_OFFICIAL rows")
    args = parser.parse_args()
    bbox = parse_bbox(args.bbox)
    where_sql = f"WHERE {bbox_sql('p.geom')}" if bbox else ""

    engine = create_engine(settings.database_url)
    sql = text(
        f"""
        WITH methods AS (
            SELECT DISTINCT tech, operator_id
            FROM ter.coverage_official
        )
        INSERT INTO ter.sample_coverage
            (sample_point_id, method, tech, operator_id, is_covered, nearest_site_id, distance_to_site_m)
        SELECT p.id,
               'B_OFFICIAL',
               m.tech,
               m.operator_id,
               EXISTS (
                   SELECT 1
                   FROM ter.coverage_official c
                   WHERE c.tech = m.tech
                     AND c.operator_id = m.operator_id
                     AND ST_Intersects(p.geom, c.geom)
               ) AS is_covered,
               NULL,
               NULL
        FROM ter.road_sample_point p
        CROSS JOIN methods m
        {where_sql};
        """
    )
    with engine.begin() as conn:
        if not args.append:
            conn.execute(text("DELETE FROM ter.sample_coverage WHERE method = 'B_OFFICIAL'"))
        conn.execute(sql, bbox_params(bbox))


if __name__ == "__main__":
    main()
